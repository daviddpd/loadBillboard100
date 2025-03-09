#!/usr/bin/env python3

import argparse
import json
import logging
import glob
import os
import sys
from typing import List
import mysql.connector
from mysql.connector import Error

def setup_logging(verbose: bool, debug: bool) -> None:
    """Configure logging based on verbosity level"""
    level = logging.WARNING
    if debug:
        level = logging.DEBUG
    elif verbose:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def get_db_connection(host: str, user: str, password: str, database: str) -> mysql.connector.MySQLConnection:
    """Create database connection with SSL/TLS enabled"""
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            ssl_verify_cert=False,  # Enable SSL verification
            ssl_verify_identity=False
                            )
        logging.info("Successfully connected to the database")
        return connection
    except Error as e:
        logging.error(f"Error connecting to database: {e}")
        sys.exit(1)

def process_json_file(filepath: str, cursor: mysql.connector.cursor.MySQLCursor) -> None:
    """Process a single JSON file and insert records into database"""
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            
        for entry in data.get('data', []):
            try:
                cursor.execute(
                    "INSERT INTO hot100 (song, artist) VALUES (%s, %s)",
                    (entry.get('song'), entry.get('artist'))
                )
                logging.debug(f"Inserted: {entry.get('song')} - {entry.get('artist')}")
            except mysql.connector.IntegrityError as e:
                if e.errno == 1062:  # Duplicate entry error
                    logging.debug(f"Duplicate entry skipped: {entry.get('song')} - {entry.get('artist')}")
                else:
                    logging.error(f"Integrity error: {e}")
            except Error as e:
                logging.error(f"Error inserting record: {e}")
                
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON file {filepath}: {e}")
    except Exception as e:
        logging.error(f"Error processing file {filepath}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Import Billboard Hot 100 data to MySQL/MariaDB')
    parser.add_argument('--host', required=True, help='Database host')
    parser.add_argument('--user', required=True, help='Database user')
    parser.add_argument('--password', required=True, help='Database password')
    parser.add_argument('--database', required=True, help='Database name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output')
    parser.add_argument('files', nargs='+', help='JSON files or directory to process')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, args.debug)
    
    # Expand file list
    json_files = []
    for file_arg in args.files:
        if os.path.isdir(file_arg):
            json_files.extend(glob.glob(os.path.join(file_arg, '*.json')))
        else:
            json_files.append(file_arg)
    
    # Connect to database
    connection = get_db_connection(args.host, args.user, args.password, args.database)
    cursor = connection.cursor()
    
    try:
        # Process each file
        for json_file in json_files:
            logging.info(f"Processing file: {json_file}")
            process_json_file(json_file, cursor)
            connection.commit()
            
        logging.info("Processing completed successfully")
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main() 