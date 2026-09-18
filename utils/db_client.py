import os
import time

import oracledb


class DbClient:
    def __init__(self):
        self.user = os.environ.get(")
        self.password = os.environ.get(")
        self.dsn = os.environ.get(
            ",
        )

    def get_otp_by_phone(self, phone, max_attempts=12, interval=5):
        """Берёт последний OTP за сегодня по телефону (без кода страны)."""
        sql = """
            SELECT otp.otp_code
              FROM tbl_otp otp
             WHERE trunc(otp.otp_date) = trunc(sysdate)
               AND otp.phone LIKE '%' || :phone
             ORDER BY otp.otp_date DESC
             FETCH FIRST 1 ROW ONLY
        """
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                with oracledb.connect(
                    user=self.user,
                    password=self.password,
                    dsn=self.dsn,
                ) as conn:
                    with conn.cursor() as cur:
                        cur.execute(sql, phone=str(phone))
                        row = cur.fetchone()
                        if row and row[0] is not None:
                            code = str(row[0]).strip()
                            print(f"✅ OTP из БД (попытка {attempt}): {code}")
                            return code
                        print(f"⏳ Попытка {attempt}: OTP для {phone} ещё нет в БД")
            except Exception as e:
                last_error = e
                print(f"⚠️ Ошибка БД (попытка {attempt}): {e}")

            if attempt < max_attempts:
                time.sleep(interval)

        raise AssertionError(
            f"❌ OTP для телефона {phone} не найден. Последняя ошибка: {last_error}"
        )
