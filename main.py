import requests
import pandas as pd
import time
import configparser
import mysql.connector
import logging

from tqdm import tqdm
from mysql.connector import Error

# =========================
# READ CONFIG
# =========================
config = configparser.ConfigParser()
config.read("config.ini")

db_config = {
    "host": config["database"]["host"],
    "user": config["database"]["user"],
    "password": config["database"]["password"],
    "database": config["database"]["database"]
}

# =========================
# MYSQL CONNECTION
# =========================
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# =========================
# LOGGING
# =========================
logging.basicConfig(
    filename="sikumbang_scraper.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# =========================
# INSERT QUERY
# =========================
INSERT_QUERY = """
INSERT IGNORE INTO sikumbang_tapera (
    id_lokasi,
    nama_perumahan,
    alamat,
    telpon,
    email,
    website,
    provinsi,
    kabupaten,
    kecamatan,
    koordinat,
    pengembang,
    jumlah_unit_subsidi,
    jumlah_unit_subsidi_terjual,
    jumlah_unit_komersil,
    jumlah_unit_komersil_terjual,
    id_rumah,
    blok,
    nomor_rumah,
    tipe_bangunan,
    status_unit,
    npwp_MK,
    nik_pemilik,
    nik_booking,
    tanggal_terjual,
    nama_tipe,
    harga,
    luas_bangunan,
    luas_lahan,
    kamar_tidur,
    kamar_mandi,
    atap,
    dinding,
    lantai,
    pondasi,
    createdAt,
    updatedAt,
    tahun
)
VALUES (
    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,%s,%s
)
"""


# =========================
# HELPER FUNCTIONS
# =========================
def parse_date(value):
    if value is None:
        return None

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.date()


def parse_year(value):
    if value is None:
        return None

    parsed = pd.to_datetime(value, errors="coerce")

    if pd.isna(parsed):
        return None

    return parsed.year


def calculate_aggregation(bangunan_list):

    jml_subsidi = 0
    jml_subsidi_terjual = 0
    jml_komersil = 0
    jml_komersil_terjual = 0

    for bgn in bangunan_list:

        tipe_bgn = str(
            bgn.get("tipeBangunan")
        ).lower()

        status_unit = str(
            bgn.get("status")
        ).lower()

        if tipe_bgn == "subsidi":

            jml_subsidi += 1

            if status_unit == "terjual":
                jml_subsidi_terjual += 1

        elif tipe_bgn == "komersil":

            jml_komersil += 1

            if status_unit == "komersil-terjual":
                jml_komersil_terjual += 1

    return {
        "jumlah_unit_subsidi": jml_subsidi,
        "jumlah_unit_subsidi_terjual": jml_subsidi_terjual,
        "jumlah_unit_komersil": jml_komersil,
        "jumlah_unit_komersil_terjual": jml_komersil_terjual
    }


def build_values(info_lokasi, bgn):

    tipe = bgn.get("tipe", {})

    created_at_raw = tipe.get("createdAt")

    return (
        info_lokasi["id_lokasi"],
        info_lokasi["nama_perumahan"],
        info_lokasi["alamat"],
        info_lokasi["telpon"],
        info_lokasi["email"],
        info_lokasi["website"],

        info_lokasi["provinsi"],
        info_lokasi["kabupaten"],
        info_lokasi["kecamatan"],

        info_lokasi["koordinat"],

        info_lokasi["pengembang"],

        info_lokasi["jumlah_unit_subsidi"],
        info_lokasi["jumlah_unit_subsidi_terjual"],
        info_lokasi["jumlah_unit_komersil"],
        info_lokasi["jumlah_unit_komersil_terjual"],

        bgn.get("idRumah"),

        bgn.get("blok", {}).get("blok")
        if bgn.get("blok")
        else None,

        bgn.get("nomor"),

        bgn.get("tipeBangunan"),
        bgn.get("status"),

        bgn.get("npwpMK"),
        bgn.get("nikPemilik"),
        bgn.get("nikBooking"),

        parse_date(
            bgn.get("tanggalTerjual")
        ),

        tipe.get("nama"),

        tipe.get("harga"),

        tipe.get("luasBangunan"),
        tipe.get("luasTanah"),

        tipe.get("kamarTidur"),
        tipe.get("kamarMandi"),

        tipe.get("spesifikasiAtap"),
        tipe.get("spesifikasiDinding"),
        tipe.get("spesifikasiLantai"),
        tipe.get("spesifikasiPondasi"),

        parse_date(
            created_at_raw
        ),

        parse_date(
            tipe.get("updatedAt")
        ),

        parse_year(
            created_at_raw
        )
    )


# =========================
# MAIN SCRAPER
# =========================
def scrape_sikumbang_all_data(limit_per_page=100):

    search_url = "https://sikumbang.tapera.go.id/ajax/lokasi/search"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://sikumbang.tapera.go.id/",
        "X-Requested-With": "XMLHttpRequest"
    }

    page_number = 1

    logger.info("START SCRAPING")

    while True:

        params = {
            "sort": "terbaru",
            "page": page_number,
            "limit": limit_per_page
        }

        try:

            response = requests.get(
                search_url,
                params=params,
                headers=headers,
                timeout=15
            )

            response.raise_for_status()

            data_list = response.json().get("data", [])

            if not data_list:

                logger.info("SCRAPING FINISHED")

                break

            inserted_page = 0
            duplicate_page = 0
            failed_page = 0

            pbar = tqdm(
                data_list,
                desc=f"Page {page_number}",
                unit="lokasi"
            )

            for lokasi in pbar:

                id_lokasi = lokasi.get("idLokasi")

                detail_url = (
                    f"https://sikumbang.tapera.go.id/"
                    f"lokasi-perumahan/{id_lokasi}/json"
                )

                try:

                    detail_resp = requests.get(
                        detail_url,
                        headers=headers,
                        timeout=10
                    )

                    if detail_resp.status_code != 200:

                        logger.warning(
                            f"DETAIL FAILED | "
                            f"id_lokasi={id_lokasi} | "
                            f"status={detail_resp.status_code}"
                        )

                        failed_page += 1

                        continue

                    detail_json = detail_resp.json()

                    detail_info = detail_json.get(
                        "detail",
                        {}
                    )

                    kantor_list = detail_info.get(
                        "kantorPemasaran",
                        []
                    )

                    kontak_utama = (
                        kantor_list[0]
                        if kantor_list
                        else {}
                    )

                    bangunan_list = detail_json.get(
                        "bangunan",
                        []
                    )

                    aggregation = calculate_aggregation(
                        bangunan_list
                    )

                    info_lokasi = {
                        "id_lokasi": id_lokasi,
                        "nama_perumahan": detail_info.get("namaPerumahan"),
                        "alamat": kontak_utama.get("alamat"),
                        "telpon": kontak_utama.get("noTelp"),
                        "email": kontak_utama.get("email"),
                        "website": kontak_utama.get("website"),

                        "provinsi": detail_info.get(
                            "wilayah",
                            {}
                        ).get("provinsi"),

                        "kabupaten": detail_info.get(
                            "wilayah",
                            {}
                        ).get("kabupaten"),

                        "kecamatan": detail_info.get(
                            "wilayah",
                            {}
                        ).get("kecamatan"),

                        "koordinat": detail_info.get(
                            "koordinatPerumahan"
                        ),

                        "pengembang": detail_info.get(
                            "pengembang",
                            {}
                        ).get("nama"),

                        **aggregation
                    }

                    inserted_count = 0
                    duplicate_count = 0

                    for bgn in bangunan_list:

                        values = build_values(
                            info_lokasi,
                            bgn
                        )

                        cursor.execute(
                            INSERT_QUERY,
                            values
                        )

                        if cursor.rowcount == 1:
                            inserted_count += 1
                            inserted_page += 1
                        else:
                            duplicate_count += 1
                            duplicate_page += 1

                    conn.commit()

                    logger.info(
                        f"SUCCESS | "
                        f"id_lokasi={id_lokasi} | "
                        f"nama={info_lokasi['nama_perumahan']} | "
                        f"inserted={inserted_count} | "
                        f"duplicate={duplicate_count}"
                    )

                    pbar.set_postfix({
                        "inserted": inserted_page,
                        "duplicate": duplicate_page,
                        "failed": failed_page
                    })

                    time.sleep(0.5)

                except Exception as e:

                    failed_page += 1

                    logger.error(
                        f"DETAIL ERROR | "
                        f"id_lokasi={id_lokasi} | "
                        f"error={str(e)}"
                    )

                    continue

            logger.info(
                f"PAGE SUMMARY | "
                f"page={page_number} | "
                f"inserted={inserted_page} | "
                f"duplicate={duplicate_page} | "
                f"failed={failed_page}"
            )

            page_number += 1

        except Exception as e:

            logger.error(
                f"PAGE ERROR | "
                f"page={page_number} | "
                f"error={str(e)}"
            )

            break


# =========================
# RUN SCRAPER
# =========================
if __name__ == "__main__":

    try:

        scrape_sikumbang_all_data(
            limit_per_page=100
        )

    except KeyboardInterrupt:

        logger.warning(
            "SCRAPING STOPPED MANUALLY"
        )

    except Exception as e:

        logger.error(
            f"FATAL ERROR | error={str(e)}"
        )

    finally:

        cursor.close()
        conn.close()

        logger.info(
            "MYSQL CONNECTION CLOSED"
        )

        print("Selesai.")