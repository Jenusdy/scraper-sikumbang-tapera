# SIKUMBANG Scraper

A web scraper for collecting subsidized housing data from TAPERA's SIKUMBANG website (https://sikumbang.tapera.go.id/).

## Description

This project scrapes information about subsidized housing (rumah subsidi) available through TAPERA (Tabungan Perumahan Rakyat) in Indonesia. The scraper collects detailed information about houses, housing complexes (perumahan), and their locations, storing the data in a MySQL database.

The data includes:
- House specifications (bedrooms, bathrooms, floors, land/building area, materials)
- Housing complex details (name, type, unit counts, coordinates)
- Regional information (province, district, sub-district, village)
- Photos (facade and floor plan)

## Requirements

- Python 3.x
- MySQL Server
- Required Python packages:
  - pandas
  - requests
  - mysql-connector-python

## Installation

1. Clone or download this repository.

2. Install the required Python packages:
   ```bash
   pip install pandas requests mysql-connector-python
   ```

3. Set up the MySQL database:
   - Create a MySQL database and user.
   - Run the `database.sql` script to create the necessary tables.

4. Configure the database connection in `config.ini`:
   ```ini
   [database]
   host=your_mysql_host
   user=your_username
   password=your_password
   database=sikumbang
   ```

## Usage

1. Ensure your MySQL server is running and the database is set up.

2. Open `Main.ipynb` in Jupyter Notebook or JupyterLab.

3. Run the cells in order to execute the scraper.

The scraper will:
- Connect to the database using the configuration from `config.ini`.
- Send requests to the SIKUMBANG API to fetch housing data page by page.
- Process the JSON responses into a pandas DataFrame.
- Insert or update the data in the MySQL database.

## Database Schema

The `rumah` table stores the scraped housing data with the following key columns:
- `id`: Unique identifier
- House details: `nama_rumah`, `harga_rumah`, `jml_kamar_tidur`, etc.
- Housing complex: `nama_perumahan`, `jenis_perumahan`, etc.
- Location: `nama_provinsi`, `nama_kabupaten`, etc.
- Timestamps: `created_at`, `updated_at`

## Notes

- The scraper respects the website's API and includes appropriate headers.
- Data is updated using `ON DUPLICATE KEY UPDATE` to handle existing records.
- The scraper stops when no more data is available or if an error occurs.

## Troubleshooting

- Ensure your MySQL server is accessible and credentials are correct.
- Check network connectivity for API requests.
- Verify that the website's API structure hasn't changed.

## License

This project is for educational purposes. Please respect the terms of service of the scraped website and TAPERA's data usage policies.