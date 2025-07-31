import ftplib
import os
import concurrent.futures
import logging
import gzip
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("logs/pubchem_bulk.log"), logging.StreamHandler()])

FTP_HOST = 'ftp.ncbi.nlm.nih.gov'
COMPOUND_DIR = '/pubchem/Compound/CURRENT-Full/SDF/'
LOCAL_DIR = './pubchem_data/Compound/SDF/'
EXTRACT_DIR = './pubchem_data/extracted/'
MAX_DOWNLOAD_SIZE = 50 * 1024 * 1024  # 50MB in bytes


def download_file(remote_file, local_file):
    """Download file from FTP (new connection for thread safety)."""
    if os.path.exists(local_file):
        logging.info(f"Skipping existing file: {local_file}")
        return local_file
    try:
        with ftplib.FTP(FTP_HOST) as ftp:
            ftp.login()
            ftp.cwd(COMPOUND_DIR)
            ftp.sendcmd("TYPE I")  # Ensure binary mode
            with open(local_file, 'wb') as f:
                ftp.retrbinary(f"RETR {remote_file}", f.write)
        logging.info(f"Downloaded: {local_file}")
        return local_file
    except Exception as e:
        logging.error(f"Error downloading {remote_file}: {e}")
        return None


def extract_data_from_sdf(sdf_path):
    """Extract structured data from SDF file."""
    data = []
    with gzip.open(sdf_path, 'rt') as f:
        content = f.read()
    blocks = content.split('$$$$\n')
    for block in blocks:
        if not block.strip():
            continue
        lines = block.split('\n')
        entry = {"name": None, "description": [], "molecular_formula": None}
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('> <PUBCHEM_IUPAC_NAME>'):
                i += 1
                if i < len(lines):
                    entry["name"] = lines[i].strip()
            elif line.startswith('> <PUBCHEM_MOLECULAR_FORMULA>'):
                i += 1
                if i < len(lines):
                    entry["molecular_formula"] = lines[i].strip()
            elif line.startswith('> <PUBCHEM_COMPOUND_SYNONYMS>'):
                i += 1
                synonyms = []
                while i < len(lines) and lines[i].strip() and not lines[i].startswith('> '):
                    synonyms.extend([s.strip() for s in lines[i].split(';') if s.strip()])
                    i += 1
                entry["description"] = synonyms
                i -= 1  # Adjust for loop increment
            i += 1
        if entry["name"] or entry["molecular_formula"]:
            data.append(entry)
    return data


def main():
    os.makedirs(LOCAL_DIR, exist_ok=True)
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    
    # Connect to FTP to list files & get sizes
    with ftplib.FTP(FTP_HOST) as ftp:
        ftp.login()
        ftp.cwd(COMPOUND_DIR)
        ftp.sendcmd("TYPE I")  # Binary mode
        
        # Parse directory listing to get file sizes
        lines = []
        ftp.dir(lines.append)  # Get directory listing
        
        file_sizes = []
        for line in lines:
            parts = line.split()
            if len(parts) < 9:
                continue
            filename = parts[-1]
            if filename.endswith(".sdf.gz"):
                try:
                    size = int(parts[4])  # File size from listing
                    file_sizes.append((filename, size))
                except ValueError:
                    continue
        
        logging.info(f"Found {len(file_sizes)} SDF files with sizes.")
        
        # Sort by size (smallest first)
        file_sizes.sort(key=lambda x: x[1])
        
        # Select files up to MAX_DOWNLOAD_SIZE
        to_download = []
        cumulative_size = 0
        for f, s in file_sizes:
            if cumulative_size + s > MAX_DOWNLOAD_SIZE:
                break
            to_download.append(f)
            cumulative_size += s
        logging.info(f"Selected {len(to_download)} files (~{cumulative_size/(1024*1024):.2f}MB).")
    
    # Download in parallel (new FTP connection per thread)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(download_file, file, os.path.join(LOCAL_DIR, file)) for file in to_download]
        downloaded_files = [fut.result() for fut in concurrent.futures.as_completed(futures) if fut.result()]
    
    # Extract data
    all_data = []
    for sdf_file in downloaded_files:
        logging.info(f"Extracting data from {sdf_file}")
        batch_data = extract_data_from_sdf(sdf_file)
        all_data.extend(batch_data)
        json_path = os.path.join(EXTRACT_DIR, os.path.basename(sdf_file).replace('.sdf.gz', '.json'))
        with open(json_path, 'w') as jf:
            json.dump(batch_data, jf, indent=4)
        logging.info(f"Saved extracted data to {json_path}")
    
    # Save combined JSON
    full_json = os.path.join(EXTRACT_DIR, 'all_compounds.json')
    with open(full_json, 'w') as fj:
        json.dump(all_data, fj, indent=4)
    logging.info(f"Full extraction saved to {full_json} (total compounds: {len(all_data)}).")


if __name__ == "__main__":
    main()
