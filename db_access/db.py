import logging
import psycopg2
import psycopg2.extras
import psycopg2.errors
from config import cfg

logger = logging.getLogger('root')
logger.debug('loading')

db_cfg = cfg["db"]
general_cfg = cfg["general"]

global_conn = None


def initiate_database_connection():
    get_database_connection()


def get_database_connection():
    global global_conn
    constring = "dbname='{}' user='{}' host='{}' password='{}'".format(
        db_cfg["database"], db_cfg["user"], db_cfg["host"], db_cfg["password"])

    if global_conn is None:
        try:
            global_conn = psycopg2.connect(constring)
            logger.debug('DB Connection established')
            return global_conn
        except:
            raise Exception("No DB connection could be established. Exiting")
    else:
        return global_conn


def get_account_registration_count() -> int:
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("""select count(*) as reg_count from tusc_account_registrations""")
    except:
        logger.exception('Failed get_account_registration_count')
        return 0

    rows = cur.fetchall()
    if len(rows) < 1:
        return 0

    if rows[0]['reg_count'] is None:
        return 0

    return int(rows[0]['reg_count'])

# TODO
# def get_stats() -> dict:
#     conn = get_database_connection()
#     cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#     try:
#         cur.execute("select sum(CAST(occ_amount AS NUMERIC)) as occ_swapped, "
#                     "sum(CAST(tusc_amount AS NUMERIC)) as tusc_swapped from transfers")
#     except:
#         logger.exception('Failed to get swap stats')
#         return {}
#
#     rows = cur.fetchall()
#
#     occ_swapped = 0
#     tusc_swapped = 0
#
#     number_of_registrations = get_account_registration_count()
#
#     if len(rows) < 1:
#         return {"occ_swapped": str(occ_swapped),
#                 "tusc_swapped": str(tusc_swapped),
#                 "occ_left_to_swap": format(Decimal(general_cfg["maximum_occ"]), 'f'),
#                 "end_of_swap_date": str(general_cfg["shut_off_date"]),
#                 "number_of_registrations": str(number_of_registrations)
#                 }
#
#     if rows[0]["occ_swapped"] is not None:
#         occ_swapped = rows[0]["occ_swapped"]
#
#     if rows[0]["tusc_swapped"] is not None:
#         tusc_swapped = rows[0]["tusc_swapped"]
#
#     occ_left_to_swap = Decimal(general_cfg["maximum_occ"]) - occ_swapped
#
#     return {
#         "occ_swapped": str(occ_swapped),
#         "tusc_swapped": str(tusc_swapped),
#         "occ_left_to_swap": format(occ_left_to_swap, 'f'),
#         "end_of_swap_date": str(general_cfg["shut_off_date"]),
#         "number_of_registrations": str(number_of_registrations)
#     }


def save_completed_registration(tusc_account_name: str,
                                tusc_public_key: str,):
    conn = get_database_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("select * from tusc_account_registrations "
                    "where tusc_account_name='" + tusc_account_name + "';")
    except:
        logger.exception('Failed to get swap stats')
        return {}

    rows = cur.fetchall()
    if len(rows) < 1: # account registration does not exist
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        q = "insert into tusc_account_registrations (tusc_account_name, tusc_public_key) " \
            "values ('{}','{}');".\
            format(tusc_account_name, tusc_public_key)

        try:
            cur.execute(q)
            conn.commit()
        except:
            logger.exception('Failed save_completed_registration: tusc_account_name = ' + tusc_account_name +
                             ', tusc_public_key = ' + tusc_public_key)
            return

    return


logger.debug('loaded')
