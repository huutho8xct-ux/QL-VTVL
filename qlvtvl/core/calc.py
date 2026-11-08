"""Tính toán tự động – mô phỏng đúng các công thức của Bộ biểu Excel kèm Hướng dẫn 07-HD/BTCTW."""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from .forms import CHE_DO, DEFAULT_QUY_GIO, LOAI_TD, PP, TT_D2, YEARS

DAT = "ĐẠT"


# ----------------------------------------------------------------- helpers
def num(v, default=0.0):
    """Chuyển giá trị nhập thành số (chấp nhận dấu phẩy thập phân kiểu Việt Nam)."""
    if v is None:
        return default
    if isinstance(v, bool):
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(" ", "")
    if not s:
        return default
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return default


def blank(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")


def isnum(v) -> bool:
    if blank(v) or isinstance(v, bool):
        return False
    return num(v, None) is not None


has_num = isnum


def s(v) -> str:
    return "" if v is None else str(v).strip()


def fmt(v, digits=2) -> str:
    """Định dạng số theo kiểu Việt Nam: 1.904,25"""
    if v is None or v == "":
        return ""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if abs(f - round(f)) < 1e-9:
        out = f"{int(round(f)):,}"
    else:
        out = f"{f:,.{digits}f}".rstrip("0").rstrip(".")
    return out.replace(",", "§").replace(".", ",").replace("§", ".")


def year_ok(v) -> bool:
    if not isnum(v):
        return False
    f = num(v)
    return 2027 <= f <= 2031 and f == int(f)


def has_pp(pp, tag) -> bool:
    return tag in s(pp)


# --------------------------------------------------------------- calculator
class Calculator:
    def __init__(self, project):
        self.p = project
        self.refresh()

    def refresh(self):
        p = self.p
        self.quy = p.quy_gio() if p else DEFAULT_QUY_GIO
        self.rows = {code: p.rows(code) for code in ("A1", "A2", "B1", "DM", "B2", "C1", "C2", "C3", "D1",
                                                     "DB", "D2")}
        R = self.rows
        self.a1 = {}
        for r in R["A1"]:
            self.a1.setdefault(s(r.get("ma")), r)
        self.a2 = {}
        for r in R["A2"]:
            self.a2.setdefault(s(r.get("ma")), r)
        self.dm = {}
        for r in R["DM"]:
            self.dm.setdefault(s(r.get("ma")), r)
        self.c1 = {}
        for r in R["C1"]:
            self.c1.setdefault(s(r.get("ma")), r)
        self.c1_count = Counter(s(r.get("ma")) for r in R["C1"] if s(r.get("ma")))
        self.c3_count = Counter(s(r.get("ma_vt")) for r in R["C3"] if s(r.get("ma_vt")))
        self.c3 = {}
        for r in R["C3"]:
            self.c3.setdefault(s(r.get("ma_vt")), r)
        self.v = {}  # row_id -> dict of computed values
        self._calc_b1()
        self._calc_b2()
        self._calc_c1()
        self._calc_c3()
        self._calc_d1()
        self._calc_db()
        self._calc_d2()

    def _vt_of_cv(self, cv):
        return s(self.a2.get(s(cv), {}).get("ma_vt"))

    # ------------------------------------------------------------------ B1
    def _calc_b1(self):
        self.b1_sl = defaultdict(float)     # tổng số SP theo mã CV
        self.b1_g = defaultdict(float)      # tổng giờ tổng theo mã CV
        for r in self.rows["B1"]:
            o = {}
            A = s(r.get("ma_cv"))
            o["ma_vt"] = self._vt_of_cv(A) if A else ""
            dm = self.dm.get(s(r.get("ma_sp"))) if s(r.get("ma_sp")) else None
            o["nhom"] = s(dm.get("nhom")) if dm else ""
            o["phut_chuan"] = num(dm.get("phut_chuan")) if dm and isnum(dm.get("phut_chuan")) else ""
            o["xn_chuan"] = s(dm.get("trang_thai")) if dm else ""
            C, D, E = r.get("so_sp"), r.get("phut_do"), r.get("gio_bo_sung")
            H, I, J, K, S_ = s(r.get("nguon_sl")), s(r.get("nguon_tg")), s(r.get("tt_tg")), s(r.get("ky")), \
                s(r.get("giai_trinh"))
            N, O = o["phut_chuan"], o["xn_chuan"]
            std_ok = isnum(N) and N > 0 and O == "Đã xác nhận" and S_ == ""
            if not A:
                P = ""
            elif std_ok:
                P = N
            elif isnum(D) and num(D) > 0 and (J == "Kiểm đếm, ước lượng thực tế" or (J == "Có định mức" and I)):
                P = num(D)
            else:
                P = ""
            o["phut_tinh"] = P
            if P == "":
                Q = ""
            elif std_ok:
                Q = "Định mức danh mục: " + s(dm.get("van_ban"))
            elif J == "Có định mức":
                Q = "Định mức: " + I
            else:
                Q = "Ước lượng thực tế" + ("; " + I if I else "")
            o["nguon_tinh"] = Q
            if not A:
                R_ = ""
            elif not o["ma_vt"]:
                R_ = "THIẾU MÃ VTVL"
            elif not H:
                R_ = "THIẾU NGUỒN SẢN LƯỢNG/CÔNG VIỆC"
            elif not K:
                R_ = "THIẾU KỲ"
            elif blank(C) and isnum(E) and num(E) > 0 and I:
                R_ = DAT
            elif blank(C):
                R_ = "THIẾU SẢN LƯỢNG"
            elif not J:
                R_ = "CHƯA CHỌN TRẠNG THÁI"
            elif isnum(N) and N > 0 and O == "Đã xác nhận" and S_ and not S_.startswith("Đã xác nhận:"):
                R_ = "CHỜ XÁC NHẬN KHÁC CHUẨN"
            elif not I and not std_ok:
                R_ = "THIẾU NGUỒN THỜI GIAN"
            elif P == "":
                R_ = "THIẾU THỜI GIAN"
            else:
                R_ = DAT
            o["canh_bao"] = R_
            if R_ != DAT:
                F = ""
            elif blank(C) and isnum(E) and num(E) > 0:
                F = 0.0
            else:
                F = num(C) * num(P) / 60
            o["gio_sp"] = F
            o["gio_tong"] = "" if F == "" else F + (num(E) if isnum(E) else 0)
            self.v[r["_id"]] = o
            if A:
                self.b1_sl[A] += num(C) if isnum(C) else 0
                self.b1_g[A] += o["gio_tong"] if o["gio_tong"] != "" else 0

    # ------------------------------------------------------------------ B2
    def _calc_b2(self):
        rows = self.rows["B2"]
        key_count = Counter((s(r.get("ma_cv")), s(r.get("cong_doan")), s(r.get("ky"))) for r in rows)
        sum_h = defaultdict(float)
        for r in rows:
            E, F, G = r.get("sp_ap_dung"), r.get("phut_truoc"), r.get("phut_sau")
            A = s(r.get("ma_cv"))
            if not A or not (isnum(E) and isnum(F) and isnum(G)) or num(F) < num(G):
                h = ""
            else:
                h = num(E) * (num(F) - num(G)) / 60
            self.v[r["_id"]] = {"gio_giam": h, "ma_vt": self._vt_of_cv(A) if A else ""}
            if A and h != "":
                sum_h[A] += h
        for r in rows:
            o = self.v[r["_id"]]
            A, B = s(r.get("ma_cv")), o["ma_vt"]
            C, D, Ei = s(r.get("loai")), s(r.get("cong_doan")), r.get("sp_ap_dung")
            F, G, H, I = r.get("phut_truoc"), r.get("phut_sau"), o["gio_giam"], r.get("gio_moi")
            J, K, L, M, S_ = s(r.get("nguon")), s(r.get("ky")), s(r.get("co_so")), s(r.get("trang_thai")), \
                s(r.get("doi_chieu"))
            if not A:
                P = ""
            elif M == "Ước lượng tham khảo":
                P = "THAM KHẢO – KHÔNG TÍNH"
            elif not B or not D or not J or not K or not L or M != "Đã kiểm chứng":
                P = "CHƯA ĐỦ CĂN CỨ"
            elif C not in LOAI_TD:
                P = "LOẠI TÁC ĐỘNG KHÔNG HỢP LỆ"
            elif S_ != "Đã đối chiếu":
                P = "CHỜ SOÁT TRÙNG"
            elif key_count[(A, D, K)] > 1:
                P = "TRÙNG CÔNG ĐOẠN"
            elif H == "" and blank(I):
                P = "THIẾU GIỜ TÁC ĐỘNG"
            elif H != "" and (blank(Ei) or num(Ei) <= 0):
                P = "THIẾU SẢN PHẨM ÁP DỤNG"
            elif H != "" and num(Ei) > self.b1_sl.get(A, 0):
                P = "SẢN PHẨM ÁP DỤNG VƯỢT B1"
            elif isnum(F) and isnum(G) and num(F) < num(G) and (blank(I) or num(I) <= 0):
                P = "THỜI GIAN TĂNG CHƯA GHI GIỜ MỚI"
            elif L == "Trước thay đổi, có điều chỉnh" and sum_h[A] > self.b1_g.get(A, 0):
                P = "GIỜ GIẢM VƯỢT GIỜ B1"
            else:
                P = DAT
            o["kiem_tra"] = P
            o["gio_giam_hl"] = "" if not A else (H if P == DAT and L == "Trước thay đổi, có điều chỉnh"
                                                 and H != "" else 0.0)
            o["gio_tang_hl"] = "" if not A else (num(I) if P == DAT and not blank(I) else 0.0)
        # B2 tổng hợp
        self.b2th = []
        seen = []
        for r in rows:
            A = s(r.get("ma_cv"))
            if A and A not in seen:
                seen.append(A)
        for A in seen:
            det = [r for r in rows if s(r.get("ma_cv")) == A]
            c = sum(num(self.v[r["_id"]]["gio_giam_hl"]) for r in det
                    if s(r.get("loai")) in ("Số hóa", "Cải tiến quy trình"))
            d = sum(num(self.v[r["_id"]]["gio_giam_hl"]) for r in det) - c
            e = sum(num(self.v[r["_id"]]["gio_tang_hl"]) for r in det)
            ok = sum(1 for r in det if self.v[r["_id"]]["kiem_tra"] == DAT)
            h = len(det)
            g = "Chưa có dòng đạt" if ok == 0 else ("Đã kiểm chứng" if ok == h else "Kiểm chứng một phần")
            i = {"Đã kiểm chứng": DAT, "Kiểm chứng một phần": "CÓ DÒNG CHƯA ĐẠT – CHỈ TÍNH DÒNG ĐẠT"}.get(
                g, "CHƯA CÓ DÒNG ĐẠT – KHÔNG TÍNH TÁC ĐỘNG")
            self.b2th.append({"_id": f"b2th-{A}", "ma_cv": A, "ma_vt": self._vt_of_cv(A), "giam_so_hoa": c,
                              "giam_khac": d, "gio_moi": e, "rong": e - c - d, "trang_thai": g, "so_dong": h,
                              "canh_bao": i})
        self.b2_net_vt = defaultdict(float)
        for t in self.b2th:
            self.b2_net_vt[t["ma_vt"]] += t["rong"]

    # ------------------------------------------------------------------ C1
    def gio_pp2(self, r):
        A, J, H = s(r.get("ma")), s(r.get("che_do")), r.get("gio_rieng")
        if not A or J not in CHE_DO:
            return ""
        if J == "Đặc thù" or not blank(H):
            if isnum(H) and num(H) > 0 and s(r.get("can_cu_quy_gio")) and s(r.get("xn_gio_rieng")) == "Đã kiểm chứng":
                return num(H)
            return ""
        return self.quy

    def _calc_c1(self):
        for r in self.rows["C1"]:
            E = self.gio_pp2(r)
            A, J, H = s(r.get("ma")), s(r.get("che_do")), r.get("gio_rieng")
            if not A:
                K = ""
            elif not J:
                K = "CHƯA CHỌN CHẾ ĐỘ LÀM VIỆC"
            elif J not in CHE_DO:
                K = "CHẾ ĐỘ KHÔNG HỢP LỆ"
            elif J == "Đặc thù" and E == "":
                K = "THIẾU GIỜ ĐẶC THÙ"
            elif not blank(H) and E == "":
                K = "GIỜ CHƯA XÁC NHẬN"
            elif E == "":
                K = "THIẾU MẪU SỐ"
            else:
                K = DAT
            self.v[r["_id"]] = {"gio_pp2": E, "kt_quy_gio": K}

    def c1_val(self, ma, key):
        r = self.c1.get(s(ma))
        return self.v[r["_id"]][key] if r else ""

    # ------------------------------------------------------------------ C3
    def _calc_c3(self):
        b1_by_vt = defaultdict(list)
        for r in self.rows["B1"]:
            b1_by_vt[self.v[r["_id"]]["ma_vt"]].append(self.v[r["_id"]])
        b2_bad_vt = Counter()
        for r in self.rows["B2"]:
            o = self.v[r["_id"]]
            if s(r.get("trang_thai")) != "Ước lượng tham khảo" and o["kiem_tra"] != DAT:
                b2_bad_vt[o["ma_vt"]] += 1
        for r in self.rows["C3"]:
            A, B = s(r.get("ma_vt")), s(r.get("pp"))
            o = {"ten_vt": s(self.c1.get(A, {}).get("ten"))}
            dat = [x for x in b1_by_vt.get(A, []) if x["canh_bao"] == DAT] if A else []
            C = "" if not A or not dat else sum(num(x["gio_tong"]) for x in dat)
            D = "" if not A else self.b2_net_vt.get(A, 0.0)
            E = "" if not A or C == "" else C + (0 if D == "" else D)
            F = self.c1_val(A, "gio_pp2") if A else ""
            if not A or "PP2" not in B or E == "" or F == "" or E < 0:
                G = ""
            else:
                G = E / F if F > 0 else ""
            N = "" if not A else sum(1 for x in b1_by_vt.get(A, []) if x["canh_bao"] != DAT)
            o.update(gio_b1=C, gio_b2=D, gio_rong=E, gio_pp2=F, nguoi_qd=G, b1_chua_dat=N)
            H, I, J, K, L = r.get("nguoi_pp1"), r.get("nguoi_pp3"), r.get("nguoi_can"), s(r.get("giai_trinh")), \
                s(r.get("trang_thai"))
            pp2 = "PP2" in B
            if not A:
                M = ""
            elif B not in PP[:6]:  # ô trống cũng báo như bộ biểu  # bộ biểu 19-10-2026 chỉ chấp nhận 6 phương án ở cột M
                M = "PHƯƠNG PHÁP KHÔNG HỢP LỆ"
            elif self.c1_count[A] > 1:
                M = "TRÙNG MÃ VTVL Ở C1"
            elif pp2 and self.c1_val(A, "kt_quy_gio") != DAT:
                M = "PP2: C1 CHƯA ĐỦ CĂN CỨ"
            elif self.c1_count[A] == 0:
                M = "MÃ VTVL CHƯA CÓ Ở C1"
            elif self.c3_count[A] > 1:
                M = "TRÙNG MÃ VTVL"
            elif pp2 and E != "" and E < 0:
                M = "GIỜ RÒNG ÂM – KIỂM TRA B2"
            elif pp2 and G == "":
                M = "PP2: THIẾU GIỜ B1 HOẶC QUỸ GIỜ"
            elif pp2 and N > 0:
                M = "PP2: CÒN DÒNG B1 CHƯA ĐẠT"
            elif pp2 and b2_bad_vt[A] > 0:
                M = "PP2: B2 CHƯA ĐỦ CĂN CỨ"
            elif "PP1" in B and blank(H):
                M = "PP1: THIẾU SỐ NGƯỜI"
            elif "PP3" in B and blank(I):
                M = "PP3: THIẾU SỐ NGƯỜI"
            elif not K:
                M = "THIẾU NGUỒN/GIẢI TRÌNH"
            elif blank(J):
                M = "CHƯA KẾT LUẬN NGƯỜI CẦN BỐ TRÍ"
            elif L != "Đã kiểm chứng":
                M = "CHỜ XÁC NHẬN NGHIỆP VỤ"
            else:
                M = DAT
            o["canh_bao"] = M
            self.v[r["_id"]] = o

    def c3_confirmed(self, ma_vt):
        """Số người cần bố trí C3 nếu đúng 1 dòng 'Đã kiểm chứng' và cảnh báo ĐẠT; ngược lại ''."""
        rows = [r for r in self.rows["C3"] if s(r.get("ma_vt")) == s(ma_vt)
                and s(r.get("trang_thai")) == "Đã kiểm chứng" and self.v[r["_id"]]["canh_bao"] == DAT]
        if len(rows) != 1:
            return ""
        j = rows[0].get("nguoi_can")
        return num(j) if isnum(j) else ""

    def suggested_need(self, r) -> float:
        """Gợi ý số người cần bố trí cho một dòng C3 (đơn vị vẫn phải kết luận, loại trùng)."""
        o = self.v.get(r["_id"]) or {}
        total = 0.0
        B = s(r.get("pp"))
        if "PP2" in B and o.get("nguoi_qd") not in ("", None):
            total += o["nguoi_qd"]
        if "PP1" in B and isnum(r.get("nguoi_pp1")):
            total += num(r.get("nguoi_pp1"))
        if "PP3" in B and isnum(r.get("nguoi_pp3")):
            total += num(r.get("nguoi_pp3"))
        return total

    # ------------------------------------------------------------------ D1
    def _calc_d1(self):
        cnt = Counter(s(r.get("ma_nl")) for r in self.rows["D1"] if s(r.get("ma_nl")))
        for r in self.rows["D1"]:
            A, B, K = s(r.get("ma_nl")), s(r.get("ma_vt")), r.get("gio_rieng")
            D = "" if not B else (num(K) if isnum(K) else self.c1_val(B, "gio_pp2"))
            E, F = r.get("gio_vtvl"), r.get("gio_khac")
            if not A:
                J = ""
            elif cnt[A] > 1:
                J = "TRÙNG MÃ NGUỒN LỰC"
            elif not s(r.get("noi_bc")):
                J = "THIẾU NƠI TÍNH BIÊN CHẾ"
            elif D == "" or blank(E) or blank(F) or not s(r.get("nguon")) or s(r.get("trang_thai")) != "Đã kiểm chứng":
                J = "Chưa đủ căn cứ"
            elif num(E) + num(F) > D:
                J = "Vượt quỹ giờ"
            else:
                J = "Đạt"
            self.v[r["_id"]] = {"gio_qd": D, "canh_bao": J}

    def existing(self, ma_vt):
        """(số người thực tế, số người quy đổi) đang bố trí cho VTVL theo D1."""
        people, qd = set(), 0.0
        for r in self.rows["D1"]:
            if s(r.get("ma_vt")) == s(ma_vt) and s(r.get("ma_nl")):
                people.add(s(r.get("ma_nl")))
                d = self.v[r["_id"]]["gio_qd"]
                if d not in ("", 0) and isnum(r.get("gio_vtvl")):
                    qd += num(r.get("gio_vtvl")) / d
        return len(people), qd

    # ------------------------------------------------------------------ DB
    def _calc_db(self):
        rows = self.rows["DB"]
        cnt = Counter((s(r.get("ma_vt")), s(r.get("nam"))) for r in rows)
        for r in rows:
            A, B, C = s(r.get("ma_vt")), r.get("nam"), r.get("bien_dong")
            G = "" if not A else self.c3_confirmed(A)
            if not A:
                I = ""
            elif not year_ok(B):
                I = "NĂM KHÔNG HỢP LỆ"
            elif cnt[(A, s(B))] > 1:
                I = "TRÙNG MÃ VTVL – NĂM"
            elif G == "":
                I = "C3 CHƯA ĐƯỢC XÁC NHẬN"
            elif not isnum(C):
                I = "THIẾU BIẾN ĐỘNG (NHẬP 0 NẾU KHÔNG ĐỔI)"
            elif G + num(C) < 0:
                I = "NHU CẦU ÂM"
            elif not s(r.get("noi_dung")) or not s(r.get("can_cu")):
                I = "THIẾU GIẢI TRÌNH/NGUỒN"
            elif s(r.get("trang_thai")) != "Đã kiểm chứng":
                I = "CHƯA KIỂM CHỨNG DỰ BÁO"
            else:
                I = DAT
            self.v[r["_id"]] = {"nguoi_c3": G, "kiem_tra": I, "nguoi_nam": G + num(C) if I == DAT else ""}

    def forecast(self, ma_vt, nam):
        hits = [r for r in self.rows["DB"] if s(r.get("ma_vt")) == s(ma_vt) and s(r.get("nam")) == s(nam)
                and self.v[r["_id"]]["kiem_tra"] == DAT]
        return self.v[hits[0]["_id"]]["nguoi_nam"] if len(hits) == 1 else ""

    # ------------------------------------------------------------------ D2
    def _calc_d2(self):
        rows = self.rows["D2"]
        cnt = Counter((s(r.get("ma_vt")), s(r.get("nam"))) for r in rows)
        for r in rows:
            A, B = s(r.get("ma_vt")), r.get("nam")
            C = "" if not A else self.forecast(A, B)
            c3 = self.v[self.c3[A]["_id"]] if A in self.c3 else {}
            K = c3.get("nguoi_qd", "") if A else ""
            Lr = self.c3[A].get("nguoi_can") if A in self.c3 else None
            L = num(Lr) if isnum(Lr) else ""
            D, G, H, I, N = r.get("co_the_bt"), r.get("de_nghi"), s(r.get("giai_trinh")), s(r.get("trang_thai")), \
                s(r.get("van_ban"))
            if not A:
                M = ""
            elif not H:
                M = "THIẾU GIẢI TRÌNH"
            elif C == "":
                M = "CHƯA CÓ DỰ BÁO NĂM"
            elif blank(D):
                M = "THIẾU NGƯỜI CÙNG ĐƠN VỊ TÍNH"
            elif not isnum(D):
                M = "C/D PHẢI TÍNH THEO NGƯỜI"
            elif C < 0 or num(D) < 0:
                M = "SỐ NGƯỜI ÂM"
            elif L != "" and abs(C - L) > 1e-9:
                M = "THAY ĐỔI SO VỚI NĂM CƠ SỞ – CÓ DỰ BÁO"
            else:
                M = "ĐỐI CHIẾU XONG"
            if not A:
                J = ""
            elif not year_ok(B):
                J = "NĂM KHÔNG HỢP LỆ"
            elif cnt[(A, s(B))] > 1:
                J = "TRÙNG MÃ VTVL – NĂM"
            elif not I:
                J = "CHƯA CHỌN TRẠNG THÁI"
            elif I not in TT_D2:
                J = "TRẠNG THÁI KHÔNG HỢP LỆ"
            elif not self._c3_ok_row(A):
                J = "C3 CHƯA ĐƯỢC XÁC NHẬN"
            elif C == "":
                J = "CHƯA CÓ DỰ BÁO NĂM ĐÃ KIỂM CHỨNG"
            elif blank(D) or blank(G) or not H:
                J = "THIẾU PHƯƠNG ÁN"
            elif M in ("THIẾU GIẢI TRÌNH", "THIẾU NGƯỜI CÙNG ĐƠN VỊ TÍNH", "C/D PHẢI TÍNH THEO NGƯỜI", "SỐ NGƯỜI ÂM"):
                J = "CHƯA ĐỦ CĂN CỨ"
            elif I == "Đang xây dựng":
                J = "ĐANG XÂY DỰNG"
            elif I == "Đã hoàn thành ở đơn vị":
                J = "SẴN SÀNG THẨM ĐỊNH"
            elif not N:
                J = "THIẾU VĂN BẢN THẨM ĐỊNH/QUYẾT ĐỊNH"
            elif I == "Đã thẩm định":
                J = "ĐÃ THẨM ĐỊNH"
            else:
                J = "ĐÃ QUYẾT ĐỊNH"
            self.v[r["_id"]] = {"nguoi_can_nam": C, "pp2_qd": K, "c3_co_so": L, "kiem_soat": M, "canh_bao": J}

    def _c3_ok_row(self, ma_vt):
        rows = [r for r in self.rows["C3"] if s(r.get("ma_vt")) == s(ma_vt)
                and s(r.get("trang_thai")) == "Đã kiểm chứng" and self.v[r["_id"]]["canh_bao"] == DAT]
        return len(rows) == 1

    # --------------------------------------------------------- generic value
    def value(self, form: str, r: dict, key: str):
        o = self.v.get(r.get("_id"))
        if form == "B2TH":
            return r.get(key, "")
        if form in ("C2",) and key == "ten_vt":
            return s(self.c1.get(s(r.get("ma_vt")), {}).get("ten"))
        if o is not None and key in o:
            return o[key]
        return r.get(key, "")

    def virtual_rows(self, form):
        return list(self.b2th) if form == "B2TH" else []

    # ------------------------------------------------------------- summary
    def summary(self) -> dict:
        R = self.rows
        hours = sum(num(self.v[r["_id"]]["gio_tong"]) for r in R["B1"] if self.v[r["_id"]]["canh_bao"] == DAT)
        delta = sum(t["rong"] for t in self.b2th)
        qd = sum(num(self.v[r["_id"]]["nguoi_qd"]) for r in R["C3"] if self.v[r["_id"]]["nguoi_qd"] != "")
        need = sum(num(r.get("nguoi_can")) for r in R["C3"] if isnum(r.get("nguoi_can")))
        people = {s(r.get("ma_nl")) for r in R["D1"] if s(r.get("ma_nl"))}
        existing_qd = 0.0
        for r in R["D1"]:
            d = self.v[r["_id"]]["gio_qd"]
            if d not in ("", 0) and isnum(r.get("gio_vtvl")):
                existing_qd += num(r.get("gio_vtvl")) / d
        by_group = defaultdict(lambda: {"vt": 0, "need": 0.0, "existing": 0.0})
        for ma, r in self.c1.items():
            if not ma:
                continue
            g = s(r.get("loai_nl")) or "Chưa phân loại"
            by_group[g]["vt"] += 1
            c3 = self.c3.get(ma)
            if c3 is not None and isnum(c3.get("nguoi_can")):
                by_group[g]["need"] += num(c3.get("nguoi_can"))
            by_group[g]["existing"] += self.existing(ma)[0]
        plan = {y: 0.0 for y in YEARS}
        avail = {y: 0.0 for y in YEARS}
        req = {y: 0.0 for y in YEARS}
        giao = {y: 0.0 for y in YEARS}
        for r in R["D2"]:
            y = int(num(r.get("nam"))) if year_ok(r.get("nam")) else None
            if y is None:
                continue
            c = self.v[r["_id"]]["nguoi_can_nam"]
            plan[y] += num(c) if c != "" else 0
            avail[y] += num(r.get("co_the_bt")) if isnum(r.get("co_the_bt")) else 0
            req[y] += num(r.get("de_nghi")) if isnum(r.get("de_nghi")) else 0
            giao[y] += num(r.get("bc_giao")) if isnum(r.get("bc_giao")) else 0
        n_vt = len([m for m in self.c1 if m])
        ok_vt = sum(1 for r in R["C3"] if self.v[r["_id"]]["canh_bao"] == DAT
                    and s(r.get("trang_thai")) == "Đã kiểm chứng")
        return {
            "nv": len([r for r in R["A1"] if s(r.get("ma"))]), "cv": len([r for r in R["A2"] if s(r.get("ma"))]),
            "vt": n_vt, "hours": hours, "delta": delta, "net": hours + delta, "qd": qd, "need": need,
            "existing": len(people), "existing_qd": existing_qd, "diff": len(people) - need,
            "by_group": dict(by_group), "plan": plan, "avail": avail, "req": req, "giao": giao,
            "ok_vt": ok_vt, "ok_ratio": (ok_vt / n_vt) if n_vt else None,
        }
