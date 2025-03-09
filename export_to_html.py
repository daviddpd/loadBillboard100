#!/usr/bin/env python3

import argparse
import logging
import sys
import urllib.parse
from pathlib import Path
import mysql.connector
from mysql.connector import Error

# Configuration for search sites
SEARCH_SITES = {
    'spotify': {
        'site': 'open.spotify.com',
        'icon': './spotify.png',
        'name': 'Spotify'
    },
    'apple_music': {
        'site': 'music.apple.com',
        'icon': './applemusic.png',
        'name': 'Apple Music'
    }
}

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
            ssl_verify_cert=False,
            ssl_verify_identity=False
        )
        logging.info("Successfully connected to the database")
        return connection
    except Error as e:
        logging.error(f"Error connecting to database: {e}")
        sys.exit(1)

def create_search_url(site_info, query):
    """Create a Google search URL with site restriction"""
    base_url = "https://www.google.com/search"
    search_query = f"{query} site:{site_info['site']}"
    params = {
        'q': search_query
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def get_html_template():
    """Return the HTML template with CSS styling"""
    return r'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Billboard Hot 100 Search Links</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background-color: #4a90e2;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .search-icon {{
            width: 16px;
            height: 16px;
            vertical-align: middle;
        }}
        a {{
            color: #4a90e2;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Billboard Hot 100 Search Links</h1>
        <table>
            <thead>
                <tr>
                    <th>Artist</th>
                    <th>Song</th>
                    <th>Apple Music</th>
                    <th>Spotify</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
</body>
</html>
'''

def create_table_row(artist, song):
    """Create a table row with search links"""
    try:
        search_query = f"{artist} {song}"
        
        # Escape any special characters in the artist and song names
        artist = artist.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        song = song.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        parts = []
        parts.append("<tr>")
        parts.append(f"<td>{artist}</td>")
        parts.append(f"<td>{song}</td>")
        
        # Apple Music link
        apple_url = create_search_url(SEARCH_SITES['apple_music'], search_query)
        parts.append(f'<td><a href="{apple_url}" target="_blank"><img src="{SEARCH_SITES["apple_music"]["icon"]}" class="search-icon" alt="{SEARCH_SITES["apple_music"]["name"]}"></a></td>')
        
        # Spotify link
        spotify_url = create_search_url(SEARCH_SITES['spotify'], search_query)
        parts.append(f'<td><a href="{spotify_url}" target="_blank"><img src="{SEARCH_SITES["spotify"]["icon"]}" class="search-icon" alt="{SEARCH_SITES["spotify"]["name"]}"></a></td>')
        
        parts.append("</tr>")
        return "\n".join(parts)
    except Exception as e:
        logging.error(f"Error creating table row for {artist} - {song}: {e}")
        return ""

def main():
    parser = argparse.ArgumentParser(description='Export Billboard Hot 100 data to HTML with search links')
    parser.add_argument('--host', required=True, help='Database host')
    parser.add_argument('--user', required=True, help='Database user')
    parser.add_argument('--password', required=True, help='Database password')
    parser.add_argument('--database', required=True, help='Database name')
    parser.add_argument('--output', '-o', required=True, help='Output HTML file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, args.debug)
    
    # Connect to database
    connection = get_db_connection(args.host, args.user, args.password, args.database)
    cursor = connection.cursor()
    
    try:
        # Query the database, ordered by artist
        cursor.execute('''
            SELECT artist, song 
            FROM hot100 
            ORDER BY artist, song
        ''')
        
        # Generate table rows
        table_rows = []
        for artist, song in cursor.fetchall():
            row = create_table_row(artist, song)
            if row:
                table_rows.append(row)
        
        if not table_rows:
            raise Exception("No valid rows were generated")
        
        # Get the template
        template = get_html_template()
        if not template:
            raise Exception("HTML template is empty")
            
        # Generate the complete HTML
        try:
            html_content = template.format(table_rows='\n'.join(table_rows))
        except Exception as e:
            logging.error(f"Error formatting HTML template: {e}")
            logging.debug(f"Number of rows: {len(table_rows)}")
            logging.debug(f"First row sample: {table_rows[0] if table_rows else 'No rows'}")
            raise
        
        # Write to file
        output_path = Path(args.output)
        output_path.write_text(html_content, encoding='utf-8')
        logging.info(f"HTML file has been generated: {output_path.absolute()}")
        
    except Error as e:
        logging.error(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        if args.debug:
            import traceback
            logging.debug(traceback.format_exc())
        sys.exit(1)
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    main() 