"""
Management command to translate all 81 tutorials from French to Vietnamese.
Updates title_vi, steps_vi, and tip_vi fields via django-modeltranslation.

Usage: python manage.py translate_tutorials_vi
"""
import json

from django.core.management.base import BaseCommand

from apps.competitions.models.tutorials import TutorialSection, Tutorial


# =============================================================================
# TRANSLATION DATA
# =============================================================================

TRANSLATIONS = {
    # =========================================================================
    # Phan 1: Huong dan su dung va Bat dau (7 bai huong dan)
    # =========================================================================
    1: {
        'title_vi': 'Huong dan su dung va Bat dau',
        'tutorials': {
            1: {
                'title_vi': 'Tao tai khoan va chon vai tro cua ban',
                'steps_vi': [
                    'Truy cap MartialComp : Truy cap martialcomp.com va nhan "Dang ky mien phi". Ban cung co the tai ung dung di dong tu Play Store hoac App Store.',
                    'Dien vao mau dang ky : Nhap ho, ten, email va mat khau. Ban cung co the dang ky bang Google, Facebook hoac Apple ID de truy cap nhanh hon.',
                    'Chon vai tro chinh cua ban : Chon vai tro cua ban: Quan ly Cau lac bo, Huan luyen vien, Trong tai, Vo sinh hoac Quan ly Lien doan. Lua chon nay quyet dinh bang dieu khien va cac chuc nang cua ban, nhung ban co the them cac vai tro khac sau.',
                    'Xac nhan email cua ban : Kiem tra hop thu den va nhan vao lien ket xac nhan. Tai khoan cua ban da duoc kich hoat va ban co the truy cap bang dieu khien ca nhan hoa cua minh.',
                ],
                'tip_vi': 'Ban co the co nhieu vai tro (vi du: huan luyen vien VA vo sinh). Chuyen doi giua cac vai tro tu menu ben bat cu luc nao.',
            },
            2: {
                'title_vi': 'Tao cau lac bo cua ban',
                'steps_vi': [
                    'Bat dau trinh huong dan tao : Tu bang dieu khien, nhan "Tao cau lac bo". Trinh huong dan cai dat 4 buoc se tu dong bat dau.',
                    'Thong tin chung : Nhap ten cau lac bo, ten viet tat, dia chi day du va thong tin lien he (dien thoai, email, trang web). Them logo cua ban o dinh dang PNG hoac JPG (kich thuoc khuyen nghi: 500x500px).',
                    'Chon cac mon vo : Chon mot hoac nhieu mon vo trong so 14+ mon co san: Karate, Judo, BJJ, Taekwondo, MMA, Kung Fu, Aikido, Kendo, Muay Thai, Boxing, Capoeira, v.v.',
                    'Tuy chinh ten mien phu cua ban : Chon dia chi duy nhat cua ban: cau-lac-bo-cua-ban.martialcomp.com. Day se la dia chi cong khai cua cau lac bo ban, moi nguoi deu co the truy cap.',
                    'Cau hinh cac tuy chon : Thiet lap gio mo cua, them mo ta va anh cua phong tap. Bat hoac tat chuc nang dang ky truc tuyen cua vo sinh.',
                ],
                'tip_vi': 'Cau lac bo cua ban duoc tao voi goi Mien phi (toi da 10 thanh vien). Tat ca cac chuc nang deu co san ngay tu dau. Nang cap len Premium khi ban vuot qua 10 thanh vien.',
            },
            3: {
                'title_vi': 'Tao lien doan cua ban',
                'steps_vi': [
                    'Yeu cau tao : Chon vai tro "Quan ly Lien doan" trong qua trinh dang ky hoac them tu phan cai dat. Dien vao mau tao voi thong tin chinh thuc cua lien doan cua ban.',
                    'Thong tin chinh thuc : Nhap ten day du, ten viet tat, quoc gia, cac mon vo quan ly, so dang ky chinh thuc va thong tin lien he.',
                    'Cau hinh trang cong khai : Tuy chinh trang cong khai cua ban: anh bia, logo, mau sac, mo ta, thu vien anh va lien ket mang xa hoi.',
                    'Xac dinh cau truc : Cau hinh cac lien doan khu vuc neu can, xac dinh cac loai thanh vien cho cac cau lac bo va phi thanh vien.',
                ],
                'tip_vi': 'Cac lien doan co khong gian quan tri mo rong de giam sat tat ca cac cau lac bo thanh vien, cac cuoc thi va cap bac.',
            },
            4: {
                'title_vi': 'Cau hinh ho so huan luyen vien cua ban',
                'steps_vi': [
                    'Truy cap ho so huan luyen vien : Tu menu ben, nhan "Ho so huan luyen vien cua toi". Neu ban chua co vai tro huan luyen vien, them no tu Cai dat > Vai tro cua toi.',
                    'Nhap bang cap cua ban : Them cac bang cap (BPJEPS, DEJEPS, CQP, v.v.), cap bac cua ban trong moi mon vo va so nam kinh nghiem.',
                    'Xac dinh cac mon vo : Chon cac mon vo ban giang day va trinh do chuyen mon cua ban trong moi mon (co ban, nang cao, thi dau).',
                    'Thiet lap lich san sang : Cho biet cac khung gio giang day hang tuan cua ban. Thong tin nay se hien thi cho cac cau lac bo dang tim huan luyen vien.',
                ],
                'tip_vi': 'Ho so huan luyen vien day du voi anh va chung chi se tang dang ke kha nang hien thi cua ban voi cac cau lac bo.',
            },
            5: {
                'title_vi': 'Cau hinh ho so trong tai cua ban',
                'steps_vi': [
                    'Kich hoat vai tro trong tai : Tu Cai dat > Vai tro cua toi, kich hoat vai tro "Trong tai". Nhap so giay phep trong tai cua ban neu co.',
                    'Them bang cap cua ban : Chi ra cap do trong tai cua ban (khu vuc, quoc gia, quoc te), cac mon vo ban co trinh do va cac chung chi.',
                    'Xac dinh chuyen mon : Kata/ky thuat, doi khang, cham diem nghe thuat... Moi chuyen mon cho phep ban tham gia cac cuoc thi tuong ung.',
                    'Nhap lich san sang : Chi ra cac khu vuc dia ly va thoi gian ban san sang cho cac cuoc thi.',
                ],
                'tip_vi': 'Cac nha to chuc cuoc thi co the tim kiem va moi ban truc tiep dua tren bang cap va lich san sang cua ban.',
            },
            6: {
                'title_vi': 'Cau hinh ho so vo sinh cua ban',
                'steps_vi': [
                    'Hoan thanh thong tin ca nhan : Nhap ngay sinh, gioi tinh, can nang (cho hang muc thi dau), chieu cao va anh dai dien.',
                    'Them cap bac hien tai : Chi ra mon vo chinh cua ban, cap bac hien tai (dai), ngay cap va to chuc cap.',
                    'Nhap giay phep : Them so giay phep lien doan, ngay het han va giay chung nhan y te hien hanh.',
                    'Lien he khan cap : Them it nhat mot lien he khan cap (bat buoc cho cac cuoc thi): ho ten, so dien thoai, moi quan he.',
                ],
                'tip_vi': 'Ho so day du la can thiet de dang ky thi dau. Can nang va cap bac se tu dong xac dinh hang muc cua ban.',
            },
            7: {
                'title_vi': 'Hieu bang dieu khien va dieu huong',
                'steps_vi': [
                    'Bang dieu khien : Bang dieu khien hien thi tong quan ca nhan hoa: su kien sap toi, tin nhan gan day, thong ke nhanh va phim tat den cac hanh dong thuong dung.',
                    'Thanh ben : Menu ben cung cap quyen truy cap vao tat ca cac phan: Thanh vien, Cuoc thi, Cap bac, Tai chinh, Lich, Cai dat. No thich ung voi vai tro dang hoat dong cua ban.',
                    'Chuyen doi vai tro : Neu ban co nhieu vai tro (vi du: huan luyen vien + vo sinh), nhan vao hinh dai dien o goc tren ben phai de chuyen doi. Bang dieu khien va menu se tu dong thich ung.',
                    'Thong bao va tin nhan : Bieu tuong chuong o goc tren ben phai hien thi thong bao cua ban: dang ky, ket qua, tin nhan. Cau hinh tuy chon thong bao trong phan cai dat.',
                    'Tim kiem tong hop : Su dung thanh tim kiem de nhanh chong tim vo sinh, cau lac bo, cuoc thi hoac su kien.',
                ],
                'tip_vi': 'Tuy chinh bang dieu khien bang cach ghim cac widget yeu thich. Phim tat Ctrl+K mo tim kiem nhanh.',
            },
        },
    },

    # =========================================================================
    # Phan 2: Quan ly Cau lac bo (10 bai huong dan)
    # =========================================================================
    2: {
        'title_vi': 'Quan ly Cau lac bo',
        'tutorials': {
            1: {
                'title_vi': 'Them vo sinh thu cong',
                'steps_vi': [
                    'Mo mau them : Tu Thanh vien > Them vo sinh, dien vao mau: ho, ten, ngay sinh, gioi tinh, email va so dien thoai.',
                    'Thong tin bo sung : Them cap bac hien tai, so giay phep, anh dinh danh (tuy chon) va giay chung nhan y te.',
                    'Gan vao nhom : Gan vo sinh vao mot hoac nhieu nhom tap luyen (vi du: Karate Nguoi lon Nang cao, Judo Thieu nhi Co ban).',
                    'Gui loi moi : Danh dau "Gui email moi" de vo sinh co the tu tao tai khoan va truy cap ho so truc tuyen cua minh.',
                ],
                'tip_vi': 'Vo sinh se nhan duoc email voi lien ket de hoan tat dang ky va tai ung dung di dong.',
            },
            2: {
                'title_vi': 'Nhap hang loat vo sinh (CSV/Excel)',
                'steps_vi': [
                    'Tai mau : Tu Thanh vien > Nhap, tai mau CSV hoac Excel. Tep chua cac cot bat buoc: Ho, Ten, Ngay_sinh, Email, va cac cot tuy chon: Cap_bac, Giay_phep, Dien_thoai.',
                    'Dien vao tep : Dien du lieu vo sinh cua ban vao tep. Ton trong cac dinh dang: ngay theo DD/MM/YYYY, cap bac dang van ban (vi du: "Dai xanh", "Dan 2").',
                    'Tai len va anh xa cot : Nhap tep. Giao dien anh xa cho phep ban lien ket moi cot cua tep voi cac truong cua MartialComp. Kiem tra lai anh xa.',
                    'Xac thuc va sua loi : MartialComp phat hien loi (trung lap, dinh dang khong hop le). Sua cac hang bi loi hoac bo qua chung. Xac nhan nhap.',
                ],
                'tip_vi': 'Ban co the nhap toi 500 vo sinh trong mot lan thao tac. Chuc nang nhap tu dong phat hien trung lap theo email hoac ho + ten + ngay sinh.',
            },
            3: {
                'title_vi': 'Quan ly ho so vo sinh',
                'steps_vi': [
                    'Truy cap ho so : Tu danh sach thanh vien, nhan vao ten vo sinh de mo ho so day du.',
                    'Xem chi tiet : Ho so hien thi: thong tin ca nhan, lich su cap bac, cac cuoc thi da tham gia, diem danh va phi.',
                    'Chinh sua thong tin : Nhan "Chinh sua" de cap nhat du lieu. Cac thay doi duoc ghi lai trong lich su.',
                    'Thao tac nhanh : Tu ho so ban co the: dang ky cuoc thi, gan cap bac, gui tin nhan, tao chung chi.',
                ],
                'tip_vi': 'Su dung bo loc nang cao (cap bac, tuoi, giay phep con hieu luc, phi da dong) de nhanh chong tim vo sinh.',
            },
            4: {
                'title_vi': 'Tao tai khoan nguoi dung cho vo sinh',
                'steps_vi': [
                    'Truy cap ho so vo sinh : Mo ho so vo sinh tuong ung tu danh sach thanh vien.',
                    'Lien ket voi tai khoan : Nhan "Tao tai khoan nguoi dung". Mot email moi se duoc gui den vo sinh voi lien ket de tao mat khau.',
                    'Thiet lap quyen : Chon nhung gi vo sinh co the lam: xem ket qua, dang ky cuoc thi, xem lich, thanh toan truc tuyen.',
                ],
                'tip_vi': 'Vo sinh chua thanh nien co the co tai khoan lien ket voi tai khoan cua phu huynh thong qua chuc nang Nhom Gia dinh.',
            },
            5: {
                'title_vi': 'Quan ly vai tro va quyen han cua cau lac bo',
                'steps_vi': [
                    'Truy cap quan ly vai tro : Tu Cai dat > Vai tro va quyen han, xem cac vai tro co san: Quan tri vien, Thu ky, Thu quy, Huan luyen vien, Thanh vien.',
                    'Gan vai tro : Chon mot thanh vien va gan vai tro cho ho. Moi vai tro cap quyen truy cap vao cac chuc nang cu the.',
                    'Tuy chinh quyen han : Cho moi vai tro, xac dinh quyen: chi doc, chinh sua, xoa, truy cap tai chinh, quan ly dang ky.',
                    'Kiem tra truy cap : Xem nhat ky hoat dong de biet ai da lam gi va khi nao trong quan tri cau lac bo.',
                ],
                'tip_vi': 'Vai tro Quan tri vien co tat ca cac quyen. Tao vai tro Thu ky voi quyen truy cap thanh vien va lich nhung khong co tai chinh.',
            },
            6: {
                'title_vi': 'Theo doi diem danh / Check-in',
                'steps_vi': [
                    'Tao buoi tap : Tu Diem danh > Buoi tap moi, chon nhom tap luyen, ngay va gio cua lop.',
                    'Diem danh theo danh sach : Hien thi danh sach thanh vien cua nhom va danh dau nguoi co mat. Diem danh chi can mot cham tren di dong.',
                    'Diem danh bang ma QR : Hien thi ma QR cua buoi tap. Vo sinh quet bang dien thoai khi den phong tap.',
                    'Xem thong ke : Xem ty le diem danh theo vo sinh, nhom va thoi gian. Xac dinh cac truong hop vang mat lien tuc.',
                ],
                'tip_vi': 'Diem danh bang ma QR la phuong phap nhanh nhat cho cac nhom lon. Ma duoc lam moi moi buoi tap de tranh gian lan.',
            },
            7: {
                'title_vi': 'Quan ly chuong trinh tap luyen',
                'steps_vi': [
                    'Tao chuong trinh : Tu Chuong trinh > Moi, xac dinh ten, mon vo, trinh do (co ban, trung cap, nang cao) va thoi gian chu ky.',
                    'Lap lich cac buoi tap : Them cac khung gio hang tuan: ngay, gio bat dau, gio ket thuc, phong/san tap, huan luyen vien phu trach.',
                    'Xac dinh noi dung : Cho moi buoi tap, them ke hoach: khoi dong, luyen ky thuat, doi luyen/randori, gian ra. Dinh kem tep hoac video.',
                    'Dang va thong bao : Dang chuong trinh. Vo sinh trong nhom nhan thong bao voi chuong trinh day du.',
                ],
                'tip_vi': 'Sao chep chuong trinh hien co de nhanh chong tao chu ky moi voi cac bien the.',
            },
            8: {
                'title_vi': 'Tao va su dung ma QR cua cau lac bo',
                'steps_vi': [
                    'Tao ma QR cau lac bo : Tu Cai dat > Ma QR, tao ma QR cua cau lac bo ban. Cho phep khach truy cap truc tiep vao trang cong khai cua ban.',
                    'Ma QR dac biet : Tao ma QR cho: dang ky truc tuyen, diem danh buoi tap, trang su kien hoac lien ket ung dung di dong.',
                    'In va trung bay : Tai ma QR chat luong cao de in. Cac dinh dang co san: PNG, SVG, PDF (A4 hoac danh thiep).',
                    'Theo doi thong ke : Xem so luot quet theo ma QR, theo ngay va theo loai. Xac dinh ma QR hieu qua nhat.',
                ],
                'tip_vi': 'Trung bay ma QR dang ky o loi vao phong tap. Moi luot quet la mot khach hang tiem nang!',
            },
            9: {
                'title_vi': 'Yeu cau gia nhap lien doan',
                'steps_vi': [
                    'Tim lien doan cua ban : Tu Cau lac bo > Gia nhap, tim lien doan theo ten, mon vo hoac quoc gia.',
                    'Gui yeu cau : Dien vao mau gia nhap: thong tin cau lac bo, so dang ky, tai lieu chung minh (dieu le, bao hiem, v.v.).',
                    'Theo doi trang thai : Yeu cau cua ban trai qua cac giai doan: Da gui > Dang xem xet > Chap thuan/Tu choi. Ban nhan thong bao o moi buoc.',
                    'Gia han moi mua : Viec gia nhap la theo mua. Loi nhac tu dong duoc gui 30 ngay truoc khi het han.',
                ],
                'tip_vi': 'Gia nhap cho phep ban truy cap cac cuoc thi chinh thuc cua lien doan va quan ly giay phep tap trung.',
            },
            10: {
                'title_vi': 'Quan ly chuyen nhuong vo sinh',
                'steps_vi': [
                    'Bat dau chuyen nhuong : Tu ho so vo sinh, nhan "Yeu cau chuyen nhuong". Chon cau lac bo dich va ly do chuyen nhuong.',
                    'Quy trinh xac thuc : Cau lac bo dich nhan yeu cau va co the chap nhan hoac tu choi. Neu co lien doan lien quan, ho cung phai xac thuc.',
                    'Chuyen nhuong co hieu luc : Sau khi duoc xac thuc, vo sinh duoc tu dong chuyen voi cap bac va lich su thi dau.',
                    'Xem lich su : Lich su chuyen nhuong hien thi trong ho so vo sinh va bao cao cau lac bo.',
                ],
                'tip_vi': 'Mot so lien doan ap dung thoi gian chuyen nhuong (cua so chuyen nhuong). MartialComp tu dong tuan thu cac quy tac nay.',
            },
        },
    },

    # =========================================================================
    # Phan 3: Cuoc thi - Tao va Cau hinh (6 bai huong dan)
    # =========================================================================
    3: {
        'title_vi': 'Cuoc thi - Tao va Cau hinh',
        'tutorials': {
            1: {
                'title_vi': 'Tao cuoc thi ca nhan',
                'steps_vi': [
                    'Bat dau tao : Tu Cuoc thi > Tao, chon loai "Ca nhan". Nhap ten, mon vo, ngay va dia diem.',
                    'Xac dinh hinh thuc : Chon hinh thuc: Doi khang (kumite, randori, sparring), Ky thuat (kata, poomsae, quyen) hoac Ket hop (ca hai).',
                    'Cau hinh hang muc : Xac dinh hang muc theo gioi tinh, do tuoi, can nang va/hoac cap bac. MartialComp cung cap mau hang muc tieu chuan theo mon vo.',
                    'Tuy chon va dang : Kich hoat cac tuy chon mong muon: dang ky truc tuyen, thanh toan, truyen hinh truc tiep, ket qua cong khai. Dang cuoc thi.',
                ],
                'tip_vi': 'Su dung cac mau hang muc (WKF, IJF, ITF...) de tiet kiem thoi gian. Ban co the tuy chinh chung sau khi tao.',
            },
            2: {
                'title_vi': 'Tao cuoc thi dong doi (Dong dien/Song Luyen)',
                'steps_vi': [
                    'Chon che do doi : Trong qua trinh tao, chon loai "Doi". Xac dinh so luong thanh vien toi thieu va toi da moi doi.',
                    'Cau hinh hinh thuc doi : Chon hinh thuc: Dong dien (kata/poomsae dong doi), Song Luyen (doi khang dinh san cho hai nguoi) hoac Doi khang doi (thay nguoi).',
                    'Xac dinh thanh phan : Chi dinh cac vai tro trong doi: so chinh thuc, so du bi, cho phep thanh phan hon hop hay khong.',
                    'Tieu chi cham diem doi : Doi voi cham diem ky thuat, xac dinh trong tai danh gia ca doi cung luc hay tung thanh vien rieng le.',
                ],
                'tip_vi': 'Che do Dong dien cho phep cham diem voi cac tieu chi dong bo dac biet (nhip do, doi hinh, bieu cam chung).',
            },
            3: {
                'title_vi': 'Cau hinh hang muc cuoc thi',
                'steps_vi': [
                    'Truy cap quan ly hang muc : Tu cuoc thi da tao, di den tab Hang muc. Nhan "Them hang muc".',
                    'Xac dinh tieu chi : Cho moi hang muc, xac dinh: gioi tinh (Nam/Nu/Hon hop), do tuoi (vi du: 12-14 tuoi), can nang (vi du: -60kg), cap bac toi thieu/toi da.',
                    'Dat ten hang muc : Dat ten ro rang: "Thieu nien Nam -52kg" hoac "Kata Nu Truong thanh Nang cao". MartialComp tu dong tao ten neu ban muon.',
                    'Sap xep hang muc : Sap xep lai hang muc bang cach keo tha de thiet lap thu tu hien thi vao ngay thi dau.',
                ],
                'tip_vi': 'Nhap hang muc tu cuoc thi truoc de tiet kiem thoi gian. Su dung tuy chon "Sao chep Thong minh" de tao cac bien the.',
            },
            4: {
                'title_vi': 'Sao chep cuoc thi hien co',
                'steps_vi': [
                    'Tim cuoc thi nguon : Tu Cuoc thi > Lich su, tim cuoc thi ban muon sao chep.',
                    'Bat dau sao chep : Nhan vao 3 dau cham > Sao chep. Chon nhung gi can sao chep: hang muc, quy dinh, cau hinh, phi.',
                    'Dieu chinh cau hinh : Sua ngay, dia diem va cac thong so can thiet. Hang muc va quy dinh duoc sao chep nguyen ban.',
                ],
                'tip_vi': 'Ly tuong cho cac cuoc thi thuong nien. Sao chep phien ban truoc va chi can cap nhat ngay.',
            },
            5: {
                'title_vi': 'Cau hinh tuy chon hien thi',
                'steps_vi': [
                    'Truy cap cau hinh hien thi : Tu cuoc thi, di den Cai dat > Hien thi va Chia se.',
                    'Dang ky truc tuyen : Bat/tat dang ky cong khai. Thiet lap ngay mo va dong dang ky.',
                    'Ket qua va xep hang : Chon ket qua cong khai thoi gian thuc, cong bo sau khi xac thuc hoac rieng tu (chi ban to chuc).',
                    'Truyen hinh truc tiep : Kich hoat che do truyen hinh va them lien ket YouTube/Twitch/Facebook Live de hien thi tren trang cong khai.',
                ],
                'tip_vi': 'Ket qua truc tiep thu hut khan gia den trang cua ban va tang kha nang hien thi cua cau lac bo hoac lien doan.',
            },
            6: {
                'title_vi': 'Cau hinh quy tac doi khang',
                'steps_vi': [
                    'Chon quy dinh : Chon quy dinh co san (WKF, IJF, ITF, IBJJF, v.v.) hoac tao quy dinh tuy chinh.',
                    'Xac dinh cham diem : Cau hinh cac hanh dong va diem: Yuko (1 diem), Waza-ari (2 diem), Ippon (3 diem), v.v. Them cac hinh phat (Shido, Hansoku, v.v.).',
                    'Cau hinh hiep dau : Xac dinh thoi gian hiep, so hiep, nghi giua hiep va dieu kien thang (diem, Ippon, bo cuoc).',
                    'Quy tac dac biet : Cau hinh cac quy tac rieng: Golden Score (gio phu), Hantei (quyet dinh cua trong tai), ket thuc som do chenh lech diem.',
                ],
                'tip_vi': 'Luu cac quy dinh tuy chinh cua ban lam mau de tai su dung cho cac cuoc thi trong tuong lai.',
            },
        },
    },

    # =========================================================================
    # Phan 4: Dang ky va Doi (7 bai huong dan)
    # =========================================================================
    4: {
        'title_vi': 'Dang ky va Doi',
        'tutorials': {
            1: {
                'title_vi': 'Dang ky vo sinh tham gia cuoc thi',
                'steps_vi': [
                    'Tim cuoc thi : Tu Cuoc thi > Mo dang ky, tim cuoc thi mong muon va nhan "Dang ky".',
                    'Chon vo sinh : Danh sach thanh vien cua ban duoc hien thi. Chon mot hoac nhieu vo sinh. MartialComp tu dong chi ra cac hang muc du dieu kien cho moi nguoi.',
                    'Xac nhan hang muc : Cho moi vo sinh, xac nhan hoac thay doi hang muc de xuat. He thong xac minh can nang, tuoi va cap bac phu hop.',
                    'Xac thuc va thanh toan : Xac nhan dang ky. Neu cuoc thi yeu cau thanh toan, tien hanh thanh toan cho tat ca cac dang ky.',
                ],
                'tip_vi': 'Vo sinh co ho so chua day du (thieu can nang, giay phep het han) se duoc canh bao bang bieu tuong do.',
            },
            2: {
                'title_vi': 'Dang ky hang loat bang bieu mau',
                'steps_vi': [
                    'Truy cap che do hang loat : Tu man hinh dang ky, nhan "Dang ky hang loat". Chon hang muc dich.',
                    'Chon nhom : Loc theo nhom tap luyen, cap bac hoac tuoi. Chon cac vo sinh du dieu kien chi bang mot nhan.',
                    'Kiem tra va dieu chinh : Man hinh kiem tra hien thi moi vo sinh voi hang muc cua ho. Sua loi neu co.',
                    'Xac nhan lo : Xac thuc tat ca cac dang ky trong mot thao tac duy nhat. Tom tat duoc gui qua email.',
                ],
                'tip_vi': 'Dang ky hang loat ly tuong cho cac cau lac bo dang ky 10+ vo sinh trong cung mot cuoc thi.',
            },
            3: {
                'title_vi': 'Tao va quan ly doi',
                'steps_vi': [
                    'Tao doi : Tu cuoc thi, nhan "Dang ky doi". Dat ten doi va chon hang muc.',
                    'Them thanh vien : Them thanh vien doi tu danh sach vo sinh. Tuan thu so luong toi thieu va toi da duoc quy dinh.',
                    'Thiet lap chinh thuc va du bi : Chi dinh chinh thuc va du bi bang cach keo tha. Thu tu thi dau co the duoc thiet lap tai day.',
                    'Xac thuc doi : Kiem tra tinh hop le cua doi (so thanh vien, hang muc ca nhan) va xac nhan dang ky.',
                ],
                'tip_vi': 'Trong cac cuoc thi dong doi, ten doi hien thi tren bang diem va ket qua chinh thuc.',
            },
            4: {
                'title_vi': 'Thay doi hang muc cua doi',
                'steps_vi': [
                    'Truy cap doi : Tu cac dang ky cua ban, tim doi can sua va nhan "Chinh sua".',
                    'Thay doi hang muc : Chon hang muc moi tu menu xo xuong. He thong xac minh doi dap ung cac tieu chi.',
                    'Xac nhan thay doi : Xac thuc. Neu cuoc thi co phi dang ky khac nhau theo hang muc, dieu chinh tu dong duoc thuc hien.',
                ],
                'tip_vi': 'Thay doi hang muc chi co the thuc hien khi dang ky con mo.',
            },
            5: {
                'title_vi': 'Yeu cau lien minh (hop nhat giua cac cau lac bo)',
                'steps_vi': [
                    'Xac dinh nhu cau : Cau lac bo cua ban khong co du thanh vien de lap doi day du? Lien minh cho phep hop nhat doi tu cac cau lac bo khac nhau.',
                    'Tao yeu cau lien minh : Tu doi chua du, nhan "De xuat lien minh". Chon cau lac bo doi tac va cac vi tri can bo sung.',
                    'Gui de xuat : Cau lac bo doi tac nhan yeu cau voi chi tiet: cuoc thi, hang muc, vi tri con trong, dieu kien.',
                    'Hoan tat lien minh : Sau khi chap nhan, doi hop nhat hien thi voi thanh vien tu ca hai cau lac bo. Doi mang ten ket hop cua hai cau lac bo.',
                ],
                'tip_vi': 'Lien minh can su chap thuan cua ban to chuc cuoc thi va neu can, cua lien doan.',
            },
            6: {
                'title_vi': 'Chap nhan/tu choi yeu cau lien minh',
                'steps_vi': [
                    'Nhan thong bao : Ban nhan thong bao yeu cau lien minh. Nhan de xem chi tiet.',
                    'Xem xet de xuat : Kiem tra: cau lac bo yeu cau, cuoc thi, hang muc, vi tri can bo sung va dieu kien de xuat.',
                    'Chap nhan hoac tu choi : Nhan "Chap nhan" de xac thuc lien minh va chon thanh vien cua ban, hoac "Tu choi" voi tin nhan giai thich.',
                ],
                'tip_vi': 'Ban co the de xuat dieu kien khac bang cach sua doi dieu kien truoc khi chap nhan.',
            },
            7: {
                'title_vi': 'Quan ly dang ky nhan duoc (duyet)',
                'steps_vi': [
                    'Truy cap bang dang ky : Tu cuoc thi, di den tab Dang ky. Xem cac dang ky theo trang thai: Cho xu ly, Da duyet, Tu choi.',
                    'Xem xet va duyet : Nhan vao dang ky de kiem tra thong tin vo sinh. Duyet tung cai hoac duyet hang loat.',
                    'Tu choi voi ly do : Truong hop tu choi, chon ly do: hang muc khong dung, giay phep khong hop le, dang ky muon, v.v.',
                    'Xuat danh sach : Xuat danh sach thi sinh hop le o dinh dang CSV hoac PDF cho viec can va quan ly ngay thi dau.',
                ],
                'tip_vi': 'Bat duyet tu dong neu ban khong muon xac thuc thu cong tung dang ky.',
            },
        },
    },

    # =========================================================================
    # Phan 5: Ngay thi dau - Doi khang (8 bai huong dan)
    # =========================================================================
    5: {
        'title_vi': 'Ngay thi dau - Doi khang',
        'tutorials': {
            1: {
                'title_vi': 'Tao bang tu dong',
                'steps_vi': [
                    'Truy cap quan ly bang : Tu cuoc thi, di den Bang > Tao tu dong. Chon cac hang muc can xu ly.',
                    'Cau hinh phan phoi : Xac dinh: so thi sinh moi bang, tach thanh vien cung cau lac bo, hat giong thu cong (tuy chon).',
                    'Tao va kiem tra : Nhan "Tao". MartialComp phan phoi thi sinh tranh doi dau noi bo cau lac bo o vong dau tien.',
                    'Dieu chinh thu cong : Neu can, di chuyen thi sinh giua cac bang bang keo tha. He thong kiem tra xung dot theo thoi gian thuc.',
                ],
                'tip_vi': 'Thuat toan phan phoi dam bao cong bang bang cach tach cac cau lac bo va can bang trinh do giua cac bang.',
            },
            2: {
                'title_vi': 'To chuc va sap xep lai cac bang',
                'steps_vi': [
                    'Tong quan bang : Man hinh bang hien thi tat ca hang muc voi so thi sinh, so bang va trang thai (nhap, da xac thuc, dang dien ra).',
                    'Chinh sua bang : Nhan vao bang de xem thi sinh. Su dung keo tha de di chuyen thi sinh sang bang khac.',
                    'Quan ly vang mat : Danh dau thi sinh vang mat hoac rut lui. He thong tu dong tinh lai cac tran dau va xep hang.',
                    'Xac thuc cac bang : Khi hai long, xac thuc cac bang. Hanh dong nay tu dong tao bang thi dau.',
                ],
                'tip_vi': 'Xac thuc bang theo tung hang muc de bat dau cac tran dau cua hang muc dau tien trong khi hoan tat cac hang muc khac.',
            },
            3: {
                'title_vi': 'Lap lich thi dau',
                'steps_vi': [
                    'Xac dinh khu vuc thi dau : Tu Lich trinh > Khu vuc, xac dinh so luong san/ring co san va ten (San 1, Ring A, v.v.).',
                    'Gan khung gio : Keo cac hang muc vao cac khu vuc va khung gio. MartialComp tu dong tinh thoi gian du kien.',
                    'Phat hien xung dot : He thong phat hien xung dot: thi sinh dang ky 2 hang muc cung luc. Su dung canh bao de dieu chinh.',
                    'Dang lich trinh : Dang lich trinh. Thi sinh, huan luyen vien va trong tai nhan thong bao voi gio tham gia.',
                ],
                'tip_vi': 'Lap ke hoach them 20% thoi gian cho moi hang muc de xu ly cac su cham tre khong the tranh khoi.',
            },
            4: {
                'title_vi': 'Su dung giao dien doi khang (cham diem truc tiep)',
                'steps_vi': [
                    'Ket noi voi khu vuc : Tren may tinh bang hoac dien thoai, mo MartialComp va chon khu vuc thi dau duoc giao. Nhap ma PIN trong tai.',
                    'Giao dien cham diem : Man hinh hien thi: 2 thi sinh (do/xanh), cac nut hanh dong (diem, hinh phat), dong ho va diem hien tai.',
                    'Cho diem : Nhan cac nut cham diem: Yuko (+1), Waza-ari (+2), Ippon (+3) cho thi sinh do hoac xanh. Diem duoc cap nhat theo thoi gian thuc.',
                    'Quan ly hinh phat : Nhan Hinh phat de cho canh cao (Shido) hoac loai (Hansoku). Cac hinh phat duoc cong don.',
                    'Ket thuc tran dau : Dong ho tu dong dung. Xac thuc ket qua (thang diem, Ippon, bo cuoc). Xep hang duoc cap nhat ngay lap tuc.',
                ],
                'tip_vi': 'Giao dien duoc toi uu hoa cho may tinh bang o che do ngang. Cac nut co kich thuoc lon de su dung nhanh va khong bi loi.',
            },
            5: {
                'title_vi': 'Che do Kiosk da san',
                'steps_vi': [
                    'Kich hoat che do Kiosk : Tu Cai dat > Che do Kiosk, kich hoat va thiet lap ma PIN cho moi khu vuc thi dau.',
                    'Cau hinh moi may tinh bang : Tren moi may tinh bang cua khu vuc, dang nhap va chon khu vuc tuong ung. Nhap PIN de khoa man hinh tai khu vuc nay.',
                    'Quan ly doc lap : Moi khu vuc hoat dong tu dong: cham diem, dong ho, hien thi. Bang diem trung tam duoc cap nhat theo thoi gian thuc.',
                    'Man hinh khan gia : Ket noi man hinh bo sung o che do "Khan gia" de hien thi diem o dinh dang lon, nhin duoc tu khan dai.',
                ],
                'tip_vi': 'Che do Kiosk ngan trong tai vo tinh dieu huong ra khoi giao dien cham diem.',
            },
            6: {
                'title_vi': 'Theo doi xep hang truc tiep',
                'steps_vi': [
                    'Bang theo doi truc tiep : Man hinh theo doi hien thi theo thoi gian thuc: tran dau dang dien ra theo khu vuc, xep hang bang, tien trinh den vong chung ket.',
                    'Loc theo hang muc : Chon hang muc de xem chi tiet: bang da hoan thanh, dang dien ra va cho xu ly, voi xep hang tam thoi.',
                    'Thong bao tu dong : He thong tu dong thong bao huan luyen vien khi thi sinh cua ho can co mat tai khu vuc thi dau.',
                ],
                'tip_vi': 'Hien thi bang theo doi tren man hinh lon tai khu vuc tiep tan de moi thi sinh deu co the theo doi tien trinh.',
            },
            7: {
                'title_vi': 'Tao vong chung ket (ban ket/chung ket)',
                'steps_vi': [
                    'Bang da hoan thanh : Khi tat ca cac bang cua hang muc hoan thanh, he thong tinh cac thi sinh vuot qua theo quy tac da dinh (hang 1 va 2 moi bang, v.v.).',
                    'Tao so do : Nhan "Tao vong chung ket". So do loai truc tiep (tu ket, ban ket, chung ket, tranh hang 3) duoc tao tu dong.',
                    'Quan ly phuc hoi : Neu quy tac cho phep, vong phuc hoi duoc tao tu dong voi cac thi sinh thua o ban ket.',
                    'Bat dau vong chung ket : Cac tran vong chung ket xuat hien trong lich trinh. Cham diem hoat dong giong nhu vong bang.',
                ],
                'tip_vi': 'So do loai truc tiep duoc tao tu dong, tranh khi co the cac tran dau giua thi sinh cung cau lac bo.',
            },
            8: {
                'title_vi': 'Quan ly le trao giai podium',
                'steps_vi': [
                    'Truy cap podium : Tu hang muc da hoan thanh, nhan "Podium". Xep hang cuoi cung duoc hien thi: Vang, Bac, Dong (va co the 2 Dong).',
                    'Hien thi tung buoc : Su dung che do "Le trao giai" de hien thi tung buoc: hang 3, roi hang 2, roi hang 1, voi hieu ung hinh anh va am thanh.',
                    'Chieu len man hinh lon : Ket noi che do Trinh chieu voi may chieu de hien thi an tuong trong le trao huy chuong.',
                    'Chia se ket qua : Podium duoc tu dong dang tren trang cuoc thi va co the chia se tren mang xa hoi.',
                ],
                'tip_vi': 'Chup anh podium va them vao cuoc thi de lam phong phu thu vien anh va mang xa hoi.',
            },
        },
    },

    # =========================================================================
    # Phan 6: Cham diem Ky thuat (6 bai huong dan)
    # =========================================================================
    6: {
        'title_vi': 'Cham diem Ky thuat',
        'tutorials': {
            1: {
                'title_vi': 'Cau hinh tieu chi cham diem',
                'steps_vi': [
                    'Truy cap tieu chi : Tu cuoc thi, di den Cham diem > Tieu chi. Chon mau co san hoac tao tieu chi rieng.',
                    'Xac dinh tieu chi : Them cac tieu chi danh gia: Ky thuat (tu the, chuyen doi), Luc (kime, dong luc), Nhip do (tempo, luu loat), Bieu cam (zanshin, tinh than).',
                    'Gan trong so : Xac dinh trong so cua moi tieu chi: vi du Ky thuat 40%, Luc 25%, Nhip do 20%, Bieu cam 15%. Tong phai bang 100%.',
                    'Xac dinh thang diem : Chon thang diem: 1-5, 1-10, 5.0-10.0 hoac tuy chinh. Xac dinh muc tang (0.1, 0.5 hoac 1).',
                ],
                'tip_vi': 'Cac mau WKF va WTF da duoc cau hinh san. Tuy chinh chung theo nhu cau cu the cua ban.',
            },
            2: {
                'title_vi': 'Gan trong tai cho cac hang muc',
                'steps_vi': [
                    'Mo bang phan cong : Tu Cham diem > Trong tai, xem danh sach trong tai da dang ky va cac hang muc can phu trach.',
                    'Phan cong theo hang muc : Keo trong tai vao cac hang muc. Xac dinh so trong tai moi hang muc (thuong la 5 hoac 7).',
                    'Kiem tra tinh trung lap : MartialComp tu dong kiem tra xung dot loi ich: trong tai khong the danh gia thi sinh tu cau lac bo cua minh.',
                    'Quan ly luan phien : Lap ke hoach luan phien trong tai giua cac hang muc de tranh met moi va dam bao cong bang.',
                ],
                'tip_vi': 'He thong phat hien thien vi phan tich su khac biet cham diem giua cac trong tai va canh bao neu trong tai cham diem qua cao hoac qua thap mot cach he thong.',
            },
            3: {
                'title_vi': 'Su dung phieu cham diem ky thuat',
                'steps_vi': [
                    'Dang nhap voi tu cach trong tai : Tren may tinh bang, dang nhap voi tai khoan trong tai. Chon hang muc duoc phan cong.',
                    'Giao dien cham diem : Man hinh hien thi thi sinh hien tai, cac tieu chi danh gia va ban phim so. Moi tieu chi co thanh truot hoac ban phim rieng.',
                    'Danh gia tung luot : Cho moi thi sinh, nhap diem cho tung tieu chi. Xac thuc danh gia truoc khi chuyen sang nguoi tiep theo.',
                    'Luu lai : Danh gia cua ban duoc luu ngay lap tuc. Ban co the sua diem khi luot chua bi khoa boi ban to chuc.',
                ],
                'tip_vi': 'Giao dien so duoc toi uu hoa de nhap nhanh tren may tinh bang. Chi can mot cham cho moi diem.',
            },
            4: {
                'title_vi': 'Cham diem ky thuat dong doi (Dong dien)',
                'steps_vi': [
                    'Hieu che do doi : Trong cham diem Dong dien, cac tieu chi bo sung xuat hien: Dong bo, Doi hinh Khong gian, Bieu cam Chung.',
                    'Danh gia ca doi : Neu duoc cau hinh nhu vay, danh gia ca doi cho moi tieu chi, bao gom dong bo.',
                    'Danh gia ca nhan + doi : Neu cau hinh danh gia hon hop, danh gia tung thanh vien rieng le ROI them diem doi cho dong bo.',
                ],
                'tip_vi': 'Trong che do Dong dien, tieu chi dong bo thuong chiem 20-30% tong diem.',
            },
            5: {
                'title_vi': 'Khoa va cong bo diem',
                'steps_vi': [
                    'Kiem tra diem : Tu bang dieu khien ban to chuc, xem diem cua tat ca trong tai cho moi thi sinh. Xac dinh chenh lech dang nghi.',
                    'Khoa luot : Nhan "Khoa" de ngan moi chinh sua. Phep tinh cuoi cung (bo diem cao nhat/thap nhat, tinh trung binh) duoc thuc hien.',
                    'Cong bo ket qua : Cong bo xep hang. Diem chi tiet theo trong tai co the an hoac hien tuy theo cau hinh cua ban.',
                    'Che do thu / reset : Truoc cuoc thi, su dung che do thu de kiem tra he thong. Reset xoa tat ca diem thu.',
                ],
                'tip_vi': 'Khoa tung luot cho phep cong bo ket qua tung luot trong khi cuoc thi van tiep dien.',
            },
            6: {
                'title_vi': 'Xem xep hang tam thoi',
                'steps_vi': [
                    'Truy cap xep hang : Tu tab Xep hang, xem xep hang thoi gian thuc voi diem theo tieu chi va diem tong.',
                    'Sap xep va loc : Sap xep theo tong diem hoac theo tieu chi cu the. Loc theo bang hoac tat ca thi sinh.',
                    'Thong ke trong tai : Xem thong ke: trung binh theo trong tai, do lech chuan, phat hien thien vi. Cong cu thiet yeu cho cong bang.',
                ],
                'tip_vi': 'Xep hang tam thoi chi hien thi cho ban to chuc va trong tai. Chi cong bo cho thi sinh sau khi khoa.',
            },
        },
    },

    # =========================================================================
    # Phan 7: Ket qua va Thanh tich (4 bai huong dan)
    # =========================================================================
    7: {
        'title_vi': 'Ket qua va Thanh tich',
        'tutorials': {
            1: {
                'title_vi': 'Xem ket qua cuoc thi',
                'steps_vi': [
                    'Tim cuoc thi : Tu menu Cuoc thi hoac trang cong khai, chon cuoc thi mong muon.',
                    'Xem ket qua : Ket qua duoc to chuc theo hang muc. Cho moi hang muc: podium, xep hang day du va chi tiet diem.',
                    'Chi tiet tran dau : Nhan vao tran dau de xem chi tiet: diem theo hiep, hinh phat, dong ho va co the video tran dau.',
                ],
                'tip_vi': 'Ket qua cong khai co the truy cap khong can tai khoan MartialComp thong qua lien ket cuoc thi.',
            },
            2: {
                'title_vi': 'Cong bo va chia se ket qua',
                'steps_vi': [
                    'Xac thuc ket qua : Tu bang dieu khien ban to chuc, xem xet ket qua moi hang muc. Nhan "Xac thuc va cong bo".',
                    'Tao lien ket cong khai : Lien ket vinh vien den trang ket qua duoc tao. Sao chep de chia se.',
                    'Chia se tren mang xa hoi : Su dung cac nut chia se tich hop de dang tren Facebook, Instagram, Twitter. Podium tu dong tao hinh anh.',
                    'Ma QR ket qua : Tao ma QR ket qua de trung bay tai dia diem cuoc thi cho khan gia.',
                ],
                'tip_vi': 'Hinh anh podium tu dong duoc dinh dang cho Instagram Stories (9:16) va Facebook (16:9).',
            },
            3: {
                'title_vi': 'Xuat ket qua (CSV/PDF)',
                'steps_vi': [
                    'Truy cap xuat : Tu Ket qua > Xuat, chon dinh dang: CSV (du lieu tho), PDF (bao cao dinh dang) hoac Excel.',
                    'Chon noi dung : Chon: Xep hang tong, Chi podium, Chi tiet theo hang muc, Bao cao huy chuong theo cau lac bo hoac Tat ca.',
                    'Tuy chinh PDF : Cho PDF, chon mau: bao cao chinh thuc (voi logo lien doan), bao cao don gian hoac bang khen.',
                ],
                'tip_vi': 'Bao cao huy chuong theo cau lac bo dac biet huu ich cho cac lien doan va nha tai tro.',
            },
            4: {
                'title_vi': 'Xem thanh tich ca nhan cua ban',
                'steps_vi': [
                    'Truy cap Thanh tich cua toi : Tu ho so vo sinh, nhan "Thanh tich". Lich su thi dau cua ban duoc hien thi.',
                    'Xem thong ke : Xem: so cuoc thi, huy chuong (vang/bac/dong), ty le thang, tien trinh theo thoi gian.',
                    'Chia se thanh tich : Tao lien ket cong khai den thanh tich cua ban hoac xuat PDF cho ho so ung tuyen hoac tai tro.',
                ],
                'tip_vi': 'Thanh tich cua ban duoc tu dong cap nhat sau moi cuoc thi. No hien thi tren ho so cong khai neu ban cho phep.',
            },
        },
    },

    # =========================================================================
    # Phan 8: Quan ly Cap bac (5 bai huong dan)
    # =========================================================================
    8: {
        'title_vi': 'Quan ly Cap bac',
        'tutorials': {
            1: {
                'title_vi': 'Cau hinh he thong cap bac',
                'steps_vi': [
                    'Truy cap cau hinh : Tu Cai dat > Cap bac, chon mon vo va xac dinh he thong cap bac cua ban.',
                    'Tao cac cap : Them cac cap theo thu tu: Dai trang, Vang, Cam, Xanh la, Xanh duong, Nau, Den Dan 1, Dan 2, v.v.',
                    'Xac dinh dieu kien : Cho moi cap bac, xac dinh: thoi gian toi thieu o cap truoc, tuoi toi thieu, so buoi tap toi thieu, co yeu cau thi hay khong.',
                    'Gan mau sac : Gan mau dai cho hien thi trong giao dien va ho so.',
                ],
                'tip_vi': 'Cac he thong cap bac tieu chuan (Judo, Karate, TKD, BJJ) da duoc cau hinh san. Ban co the tuy chinh hoac tao moi.',
            },
            2: {
                'title_vi': 'Gan cap bac cho vo sinh',
                'steps_vi': [
                    'Truy cap ho so : Tu ho so vo sinh, nhan tab Cap bac roi "Gan cap bac moi".',
                    'Chon cap bac : Chon cap bac tu danh sach. He thong tu dong kiem tra dieu kien (thoi gian, tuoi, ky thi).',
                    'Nhap chi tiet : Them ngay gan, dia diem, hoi dong/giam khao va nhan xet.',
                    'Gan hang loat : Tu Cap bac > Gan hang loat, chon nhieu vo sinh va gan cung cap bac cho tat ca.',
                ],
                'tip_vi': 'Email chuc mung duoc tu dong gui den vo sinh voi cap bac moi cua ho.',
            },
            3: {
                'title_vi': 'To chuc ky thi len cap',
                'steps_vi': [
                    'Tao ky thi : Tu Cap bac > Ky thi, tao ky thi moi: ngay, dia diem, mon vo, cac cap bac duoc thi, hoi dong.',
                    'Dang ky thi sinh : Them thi sinh thu cong hoac cho phep tu dang ky. He thong kiem tra dieu kien cua moi nguoi.',
                    'Ngay thi : Su dung giao dien ky thi de danh gia moi thi sinh: ky thuat yeu cau, doi khang, ly thuyet.',
                    'Cong bo ket qua : Xac thuc dat va khong dat. Cap bac duoc tu dong gan cho cac thi sinh dat.',
                ],
                'tip_vi': 'Ky thi cap bac co the lien ket voi cuoc thi (vi du: len cap trong giai dau).',
            },
            4: {
                'title_vi': 'Quan ly lich su va tien trinh cap bac',
                'steps_vi': [
                    'Xem lich su : Ho so moi vo sinh hien thi lich su cap bac day du: ngay, dia diem, hoi dong, nhan xet.',
                    'Hien thi tien trinh : Bieu do hien thi tien trinh theo thoi gian. So sanh voi trung binh cau lac bo.',
                    'Thu hoi cap bac : Truong hop nham lan, thu hoi cap bac voi ly do. Lich su luu giu ban ghi thu hoi.',
                ],
                'tip_vi': 'Lich su cap bac co the chuyen khi vo sinh doi cau lac bo.',
            },
            5: {
                'title_vi': 'Tao chung chi cap bac',
                'steps_vi': [
                    'Truy cap chung chi : Tu Cap bac > Chung chi, chon vo sinh va cap bac can tao chung chi.',
                    'Chon mau : Chon mau chung chi: chinh thuc (voi logo lien doan), cau lac bo hoac tuy chinh.',
                    'Tuy chinh : Them chu ky, con dau cau lac bo va cac ghi chu dac biet. Ma QR xac minh duoc tu dong them.',
                    'Tao va phan phoi : Tao PDF. In hoac gui qua email. Ma QR cho phep bat ky ai xac minh tinh xac thuc cua chung chi.',
                ],
                'tip_vi': 'Ma QR xac minh dan den trang cong khai cua MartialComp xac nhan tinh hop le cua cap bac.',
            },
        },
    },

    # =========================================================================
    # Phan 9: Quan ly Lien doan (8 bai huong dan)
    # =========================================================================
    9: {
        'title_vi': 'Quan ly Lien doan',
        'tutorials': {
            1: {
                'title_vi': 'Quan ly cac cau lac bo thanh vien',
                'steps_vi': [
                    'Tong quan : Bang dieu khien lien doan hien thi ban do cac cau lac bo thanh vien, trang thai (hoat dong, cho xu ly, het han) va thong ke.',
                    'Xu ly yeu cau : Cac yeu cau gia nhap moi xuat hien tai Cau lac bo > Cho xu ly. Xem tai lieu va duyet hoac tu choi.',
                    'Theo doi gia han : Xem cac thanh vien sap het han. Gui nhac nho tu dong 30, 15 va 7 ngay truoc.',
                ],
                'tip_vi': 'Bang dieu khien lien doan cung cap tam nhin thoi gian thuc ve tong so vo sinh co giay phep tai tat ca cau lac bo.',
            },
            2: {
                'title_vi': 'Quan ly mua giai va phi',
                'steps_vi': [
                    'Tao mua giai : Tu Mua giai > Moi, xac dinh ngay bat dau va ket thuc va phi theo loai (cau lac bo, ca nhan, thieu nien, nguoi lon).',
                    'Cau hinh phi : Xac dinh so tien theo loai: phi cau lac bo (co dinh), giay phep ca nhan (theo vo sinh), bao hiem (tuy chon).',
                    'Theo doi thanh toan : Xem phi da nhan, cho xu ly va qua han theo thoi gian thuc. Gui nhac nho tu dong.',
                    'Dong mua giai : Cuoi mua giai, dong de tao bao cao tai chinh va chuan bi mua giai tiep theo.',
                ],
                'tip_vi': 'Phi co the thanh toan truc tuyen qua Stripe hoac chuyen khoan ngan hang. Theo doi tu dong trong ca hai truong hop.',
            },
            3: {
                'title_vi': 'Giam sat cac cuoc thi',
                'steps_vi': [
                    'Tam nhin tong the : Lich lien doan hien thi tat ca cac cuoc thi cua cac cau lac bo thanh vien, voi trang thai va so thi sinh.',
                    'Cong nhan cuoc thi : Cac cau lac bo gui cuoc thi de cong nhan. Kiem tra quy tac, trong tai va xac thuc.',
                    'Xem ket qua : Truy cap ket qua cua tat ca cuoc thi da cong nhan. Xep hang quoc gia duoc tu dong cap nhat.',
                ],
                'tip_vi': 'Cac cuoc thi duoc lien doan cong nhan duoc noi bat trong danh muc va lich cong khai.',
            },
            4: {
                'title_vi': 'Quan ly trong tai va bang cap',
                'steps_vi': [
                    'Co so du lieu trong tai : Xem co so du lieu trong tai thanh vien voi bang cap, chuyen mon va lich su hoat dong.',
                    'Quan ly cap do : Gan cap do trinh do: khu vuc, quoc gia, quoc te. Xac dinh tieu chi thang tien.',
                    'Theo doi tinh trung lap : MartialComp phan tich thong ke cham diem cua moi trong tai va phat hien thien vi tiem nang.',
                ],
                'tip_vi': 'Trong tai co lich su cham diem can bang duoc uu tien cho cac cuoc thi quan trong.',
            },
            5: {
                'title_vi': 'Quan ly chung nhan',
                'steps_vi': [
                    'Tao mau : Thiet ke mau chung nhan voi logo lien doan, thong tin phap ly va cac truong dong.',
                    'Cap chung nhan : Tao chung nhan cho: cap bac, trinh do trong tai, bang giang day, cac chung chi khac nhau.',
                    'Xac minh cong khai : Moi chung nhan co ma QR duy nhat. Bat ky ai cung co the quet de xac minh tinh xac thuc tren martialcomp.com.',
                ],
                'tip_vi': 'Chung nhan so khong the gia mao nho ma QR xac minh lien ket voi MartialComp.',
            },
            6: {
                'title_vi': 'Tuy chinh trang cong khai cua lien doan',
                'steps_vi': [
                    'Truy cap trinh tao trang : Tu Cai dat > Trang cong khai, mo trinh chinh sua trang. Lien doan cua ban co URL: lien-doan.martialcomp.com.',
                    'Tuy chinh giao dien : Chon mau sac, chu de, anh bia va logo. Them mo ta va lien ket mang xa hoi.',
                    'Them noi dung : Dang tin tuc, thu vien anh, video, lich cuoc thi va tai lieu tai xuong.',
                    'Quan ly trang : Tao cac trang bo sung: Lich su, Ban lanh dao, Dieu le, Lien he.',
                ],
                'tip_vi': 'Trang cong khai duoc toi uu hoa cho SEO. Cang day du noi dung, cang xep hang tot tren Google.',
            },
            7: {
                'title_vi': 'Xem thong ke va bao cao',
                'steps_vi': [
                    'Bang phan tich : Bang dieu khien hien thi cac KPI: so cau lac bo, vo sinh, cuoc thi, giay phep hoat dong, tang truong.',
                    'Bao cao theo cau lac bo : Tao bao cao chi tiet theo cau lac bo: so thanh vien, phi, tham gia cuoc thi, cap bac duoc cap.',
                    'Bao cao theo mon vo : Phan tich phan phoi theo mon vo, tuoi, gioi tinh. Xac dinh xu huong tang truong.',
                    'Xuat va chia se : Xuat bao cao dang PDF, Excel hoac CSV cho dai hoi va bao cao chinh thuc.',
                ],
                'tip_vi': 'Bao cao duoc cap nhat theo thoi gian thuc. Dat lich gui tu dong hang thang hoac hang quy.',
            },
            8: {
                'title_vi': 'Quan ly chuong trinh dao tao',
                'steps_vi': [
                    'Tao chuong trinh : Tu Dao tao > Moi, xac dinh chuong trinh: tieu de, mon vo, trinh do, thoi gian, dieu kien.',
                    'Lap lich cac buoi : Them cac buoi dao tao: ngay, dia diem, giang vien, so cho.',
                    'Quan ly dang ky : Huan luyen vien va trong tai dang ky truc tuyen. Xac thuc dang ky va gui giay moi.',
                    'Theo doi va cap chung chi : Theo doi diem danh cac buoi. Cap chung chi cho cac thi sinh hoan thanh chuong trinh.',
                ],
                'tip_vi': 'Cac chuong trinh dao tao hoan thanh tu dong hien thi tren ho so cua huan luyen vien va trong tai.',
            },
        },
    },

    # =========================================================================
    # Phan 10: Tai chinh (5 bai huong dan)
    # =========================================================================
    10: {
        'title_vi': 'Tai chinh',
        'tutorials': {
            1: {
                'title_vi': 'Theo doi giao dich cua cau lac bo',
                'steps_vi': [
                    'Tong quan : Bang tai chinh hien thi: so du, thu nhap thang, chi phi va bieu do xu huong.',
                    'Ghi nhan giao dich : Them thu hoac chi: so tien, ngay, loai (phi, thiet bi, thue), mo ta.',
                    'Phan loai tu dong : MartialComp tu dong phan loai cac giao dich dinh ky. Tuy chinh cac loai theo nhu cau.',
                ],
                'tip_vi': 'Ket noi tai khoan ngan hang de tu dong nhap giao dich va don gian hoa doi soat.',
            },
            2: {
                'title_vi': 'Tao va gui hoa don',
                'steps_vi': [
                    'Tao hoa don : Tu Tai chinh > Hoa don > Moi, chon nguoi nhan (vo sinh, cau lac bo, nha tai tro) va cac dong hoa don.',
                    'Tuy chinh : Them logo, thong tin phap ly, dieu khoan thanh toan. Chon don vi tien te va thue suat.',
                    'Gui : Gui hoa don qua email. Nguoi nhan nhan lien ket thanh toan truc tuyen (Stripe) va hoa don PDF.',
                    'Theo doi thanh toan : Xem hoa don da thanh toan, cho xu ly va qua han. Gui nhac nho tu dong.',
                ],
                'tip_vi': 'Phi vo sinh tu dong tao hoa don neu ban kich hoat tuy chon nay.',
            },
            3: {
                'title_vi': 'Quan ly thanh toan truc tuyen (Stripe)',
                'steps_vi': [
                    'Ket noi Stripe : Tu Cai dat > Thanh toan, nhan "Ket noi Stripe". Lam theo cac buoc de lien ket tai khoan Stripe cua ban.',
                    'Cau hinh thanh toan : Thiet lap phi cho: hoi phi, dang ky cuoc thi, cua hang. Kich hoat thanh toan dinh ky neu can.',
                    'Thu thanh toan : Su dung che do thu cua Stripe de xac minh moi thu hoat dong truoc khi kich hoat thanh toan thuc.',
                    'Theo doi doanh thu : Bang Stripe trong MartialComp hien thi cac khoan thanh toan da nhan, hoan tien va chuyen khoan vao tai khoan ngan hang.',
                ],
                'tip_vi': 'Stripe tinh phi 1,4% + 0,25 EUR moi giao dich tai Chau Au. Tien duoc chuyen trong 2-7 ngay.',
            },
            4: {
                'title_vi': 'Nhap sao ke ngan hang',
                'steps_vi': [
                    'Tai sao ke : Tu ngan hang cua ban, xuat sao ke o dinh dang CSV, OFX hoac QIF.',
                    'Nhap vao MartialComp : Tu Tai chinh > Nhap, tai tep len. MartialComp phat hien dinh dang va anh xa cac cot.',
                    'Doi soat : He thong tu dong khop cac giao dich nhap voi hoa don va phi hien co.',
                    'Xac thuc : Kiem tra cac khop noi, sua loi va xac thuc. Cac giao dich chua khop duoc them vao danh sach cho xu ly.',
                ],
                'tip_vi': 'Nhap sao ke ngan hang hang thang giup ke toan cua ban luon cap nhat ma khong can nhap thu cong.',
            },
            5: {
                'title_vi': 'Quan ly hoi phi cua vo sinh',
                'steps_vi': [
                    'Cau hinh phi : Tu Tai chinh > Hoi phi, thiet lap phi hang nam theo loai: thieu nhi, thieu nien, nguoi lon, gia dinh.',
                    'Phat hanh yeu cau thanh toan : Dau mua giai, tao yeu cau thanh toan cho tat ca thanh vien. Moi nguoi nhan email voi lien ket thanh toan.',
                    'Theo doi thanh toan : Xem hoi phi da thanh toan, cho xu ly va qua han. Trang thai hien thi trong ho so moi vo sinh.',
                    'Gui nhac nho : Dat lich nhac nho tu dong: 1 tuan, 2 tuan, 1 thang sau ngay het han.',
                ],
                'tip_vi': 'Vo sinh co hoi phi qua han co the bi chan khoi dang ky cuoc thi.',
            },
        },
    },

    # =========================================================================
    # Phan 11: Su kien va Lich (3 bai huong dan)
    # =========================================================================
    11: {
        'title_vi': 'Su kien va Lich',
        'tutorials': {
            1: {
                'title_vi': 'Tao su kien (hoi thao, bieu dien, dai hoi)',
                'steps_vi': [
                    'Tao su kien : Tu Lich > Su kien moi, nhap: loai (hoi thao, bieu dien, dai hoi, ngay hoi mo cua), tieu de, ngay, dia diem va mo ta.',
                    'Cau hinh dang ky : Bat dang ky truc tuyen. Thiet lap so cho, phi (mien phi hoac co phi) va han dang ky.',
                    'Dang : Dang su kien. No xuat hien trong lich cau lac bo va co the chia se tren mang xa hoi.',
                ],
                'tip_vi': 'Hoi thao voi su phu khach moi la cong cu marketing tuyet voi. Them anh va tieu su cua ho de thu hut nhieu nguoi hon.',
            },
            2: {
                'title_vi': 'Quan ly su kien dinh ky',
                'steps_vi': [
                    'Tao dinh ky : Trong qua trinh tao, danh dau "Su kien dinh ky". Thiet lap tan suat: hang ngay, hang tuan, hang thang.',
                    'Quan ly ngoai le : Huy hoac sua mot lan cu the ma khong anh huong den cac lan khac (vi du: lop huy vi ngay le).',
                    'Sua chuoi : Sua toan bo chuoi (vi du: doi gio vinh vien) hoac chi mot lan cu the.',
                ],
                'tip_vi': 'Cac lop hang tuan nen duoc tao nhu su kien dinh ky de tu dong hien thi trong lich.',
            },
            3: {
                'title_vi': 'Theo doi dang ky va diem danh su kien',
                'steps_vi': [
                    'Xem nguoi dang ky : Tu su kien, xem danh sach nguoi dang ky voi trang thai: da dang ky, da xac nhan, da huy.',
                    'Ghi nhan diem danh : Ngay dien ra su kien, ghi nhan diem danh bang danh sach hoac ma QR.',
                    'Xuat : Xuat danh sach tham gia dang CSV hoac PDF cho ho so cua ban.',
                ],
                'tip_vi': 'Ty le tham gia su kien la chi so quan trong ve muc do gan ket cua thanh vien.',
            },
        },
    },

    # =========================================================================
    # Phan 12: Quan ly Gia dinh (3 bai huong dan)
    # =========================================================================
    12: {
        'title_vi': 'Quan ly Gia dinh',
        'tutorials': {
            1: {
                'title_vi': 'Tao nhom gia dinh',
                'steps_vi': [
                    'Truy cap nhom gia dinh : Tu ho so cua ban, di den Cai dat > Nhom Gia dinh > Tao.',
                    'Them thanh vien : Them tung thanh vien gia dinh: vo/chong, con cai. Lien ket tai khoan MartialComp hien co hoac tao tai khoan moi.',
                    'Thiet lap nguoi phu trach : Nguoi phu trach nhom gia dinh nhan tat ca thong bao va quan ly thanh toan cho ca gia dinh.',
                ],
                'tip_vi': 'Mot so cau lac bo cung cap gia gia dinh (giam gia tu thanh vien thu 3). Nhom gia dinh tu dong kich hoat cac uu dai nay.',
            },
            2: {
                'title_vi': 'Dang ky ca gia dinh tham gia cuoc thi',
                'steps_vi': [
                    'Dang ky nhom : Tu cuoc thi, nhan "Dang ky gia dinh toi". Cac thanh vien du dieu kien trong nhom gia dinh duoc hien thi.',
                    'Chon va xac nhan : Chon cac thanh vien can dang ky. Hang muc duoc tu dong goi y cho moi nguoi.',
                    'Thanh toan mot lan : Thanh toan tat ca dang ky trong mot giao dich duy nhat.',
                ],
                'tip_vi': 'Dang ky nhom tiet kiem thoi gian quy bau khi nhieu con tham gia cung mot cuoc thi.',
            },
            3: {
                'title_vi': 'Trung tam thanh toan gia dinh',
                'steps_vi': [
                    'Tong quan : Trung tam gia dinh hien thi tat ca hoi phi, dang ky va hoa don cua gia dinh tren mot man hinh.',
                    'Thanh toan gop : Gop nhieu khoan thanh toan cho xu ly va thanh toan trong mot giao dich duy nhat.',
                    'Lich su : Xem lich su thanh toan day du cua gia dinh voi bien lai co the tai xuong.',
                ],
                'tip_vi': 'Kich hoat ghi no tu dong de khong bao gio quen hoi phi.',
            },
        },
    },

    # =========================================================================
    # Phan 13: Quan ly Cong viec (Kanban) (2 bai huong dan)
    # =========================================================================
    13: {
        'title_vi': 'Quan ly Cong viec (Kanban)',
        'tutorials': {
            1: {
                'title_vi': 'Su dung bang Kanban',
                'steps_vi': [
                    'Tao bang : Tu Cong cu > Kanban, tao bang moi: ten, mo ta va thanh vien duoc moi.',
                    'Them cot : Tao cac cot quy trinh lam viec: Can lam, Dang lam, Cho doi, Hoan thanh. Tuy chinh ten va mau sac.',
                    'Tao cong viec : Them cong viec voi: tieu de, mo ta, han chot, nguoi phu trach, uu tien (cao/trung binh/thap) va nhan.',
                    'Quan ly bang keo tha : Di chuyen cong viec giua cac cot bang cach keo. Lich su di chuyen duoc luu giu.',
                ],
                'tip_vi': 'Tao bang rieng cho moi cuoc thi can to chuc. Cac cong viec tieu chuan (dat dia diem, dat huy chuong, v.v.) co the nhap tu mau.',
            },
            2: {
                'title_vi': 'Quan ly cong viec to chuc',
                'steps_vi': [
                    'Mau cuoc thi : Su dung mau "To chuc Cuoc thi" chua cac cong viec tieu chuan: hau can, truyen thong, trong tai, huy chuong, v.v.',
                    'Phan cong cho thanh vien : Phan cong moi cong viec cho thanh vien doi to chuc. Dat han chot.',
                    'Theo doi tien do : Ty le tien do tong the hien thi o dau bang. Cac cong viec qua han duoc to do.',
                ],
                'tip_vi': 'Bang Kanban co the truy cap tu ung dung di dong de cap nhat cong viec moi luc.',
            },
        },
    },

    # =========================================================================
    # Phan 14: Cua hang Truc tuyen (2 bai huong dan)
    # =========================================================================
    14: {
        'title_vi': 'Cua hang Truc tuyen',
        'tutorials': {
            1: {
                'title_vi': 'Cau hinh cua hang cua cau lac bo',
                'steps_vi': [
                    'Kich hoat cua hang : Tu Cai dat > Cua hang, kich hoat chuc nang thuong mai dien tu. Ket noi tai khoan Stripe neu chua co.',
                    'Them san pham : Tao san pham: ten, mo ta, anh, gia, kich co/bien the co san, ton kho.',
                    'Phan loai : Phan loai san pham: Dong phuc (vo phuc, dobok, gang tay), Thiet bi (bao ho, tui), Phu kien (dai, phu hieu), Hang luu niem.',
                    'Dang cua hang : Cua hang cua ban co the truy cap tu trang cong khai cau lac bo. Chia se lien ket hoac ma QR.',
                ],
                'tip_vi': 'Cung cap goi (vo phuc + dai + tui) voi giam gia de tang gia tri don hang trung binh.',
            },
            2: {
                'title_vi': 'Dat hang',
                'steps_vi': [
                    'Duyet cua hang : Tu trang cau lac bo, truy cap cua hang. Duyet san pham theo loai.',
                    'Them vao gio hang : Chon kich co/bien the va them vao gio. Gio hang duoc luu giua cac phien.',
                    'Dat hang va thanh toan : Xac nhan gio hang, chon phuong thuc giao hang (nhan tai phong tap hoac gui buu dien) va thanh toan truc tuyen.',
                    'Theo doi don hang : Nhan thong bao o moi buoc: don hang da xac nhan, dang chuan bi, san sang nhan / da gui.',
                ],
                'tip_vi': 'Che do "Nhan tai Phong tap" giup tiet kiem phi van chuyen. Huan luyen vien se giao don hang cho ban tai buoi tap tiep theo.',
            },
        },
    },

    # =========================================================================
    # Phan 15: Chuc nang Nang cao (5 bai huong dan)
    # =========================================================================
    15: {
        'title_vi': 'Chuc nang Nang cao',
        'tutorials': {
            1: {
                'title_vi': 'Cau hinh truyen hinh truc tiep cuoc thi',
                'steps_vi': [
                    'Chuan bi truyen hinh : Tao su kien truc tiep tren YouTube, Twitch hoac Facebook. Sao chep URL truyen hinh va khoa truyen hinh.',
                    'Cau hinh tren MartialComp : Tu cuoc thi, di den Cai dat > Truyen hinh. Dan URL va kich hoat hien thi tren trang cong khai.',
                    'Lop phu diem : Kich hoat lop phu MartialComp hien thi diem truc tiep tren truyen hinh video. Tuy chinh vi tri va kieu.',
                    'Bat dau va thu : Bat dau truyen hinh va xac minh lop phu hoat dong. Khan gia se thay diem truc tiep tren truyen hinh.',
                ],
                'tip_vi': 'Truyen hinh voi lop phu diem MartialComp mang lai ve chuyen nghiep ngay ca cho cac cuoc thi nho.',
            },
            2: {
                'title_vi': 'Su dung ung dung di dong',
                'steps_vi': [
                    'Tai ung dung : Tim "MartialComp" tren Play Store (Android) hoac App Store (iOS). Cai dat va mo.',
                    'Dang nhap : Dang nhap voi tai khoan MartialComp hien co. Ban cung co the su dung dang nhap Google, Facebook hoac Apple.',
                    'Kham pha giao dien di dong : Ung dung cung cap: ho so, ket qua, lich, thong bao day, ma QR ca nhan va dang ky cuoc thi.',
                    'Che do ngoai tuyen : Du lieu thiet yeu (ho so, cap bac, giay phep) co san khi khong co mang. Tu dong dong bo khi ket noi lai.',
                ],
                'tip_vi': 'Bat thong bao day de nhan canh bao ket qua truc tiep trong cac cuoc thi.',
            },
            3: {
                'title_vi': 'Chuyen doi vai tro trong ung dung',
                'steps_vi': [
                    'Truy cap bo chon vai tro : Cham vao hinh dai dien o dau man hinh hoac vuot tu trai de mo menu ben.',
                    'Chon vai tro : Danh sach vai tro cua ban hien thi: Huan luyen vien, Vo sinh, Trong tai, Quan ly Cau lac bo. Cham vao vai tro mong muon.',
                    'Giao dien thich ung : Bang dieu khien va menu duoc cap nhat ngay lap tuc de phan anh vai tro da chon.',
                ],
                'tip_vi': 'Ban co the la huan luyen vien o mot cau lac bo va vo sinh o cau lac bo khac. Moi vai tro duoc lien ket voi to chuc cua no.',
            },
            4: {
                'title_vi': 'Nhap/Xuat du lieu nang cao',
                'steps_vi': [
                    'Cac dinh dang ho tro : MartialComp ho tro nhap va xuat CSV, Excel (XLSX), JSON va PDF. Moi module co cac tuy chon rieng.',
                    'Nhap voi anh xa : Giao dien anh xa cho phep lien ket bat ky cau truc tep nao voi cac truong cua MartialComp.',
                    'Xuat tuy chinh : Chon cac truong can xuat, bo loc va dinh dang. Dat lich xuat tu dong dinh ky.',
                    'Thao tac hang loat : Thao tac hang loat cho phep chinh sua hang loat: cap bac, nhom, trang thai dang ky, v.v.',
                ],
                'tip_vi': 'Xuat JSON ly tuong cho tich hop voi he thong ben thu ba (trang web, ung dung ben ngoai, CRM).',
            },
            5: {
                'title_vi': 'Quan ly trong tai tam thoi (tinh nguyen)',
                'steps_vi': [
                    'Tao trong tai tam thoi : Ngay thi dau, tu Trong tai > Them tinh nguyen vien, tao ho so tam thoi: ten, cau lac bo va chuyen mon.',
                    'Gan ma PIN : Ma PIN duy nhat duoc tu dong tao. Tinh nguyen vien su dung PIN nay de truy cap giao dien cham diem.',
                    'Phan cong hang muc : Phan cong trong tai tinh nguyen vao cac hang muc nhu trong tai chinh thuc. Ho co the bat dau danh gia ngay lap tuc.',
                    'Sau cuoc thi : Ho so tam thoi duoc luu tru sau cuoc thi. Cac diem cham duoc giu trong lich su.',
                ],
                'tip_vi': 'Trong tai tam thoi la thiet yeu cho cac cuoc thi nho noi so luong trong tai chinh thuc con han che.',
            },
        },
    },
}


class Command(BaseCommand):
    help = 'Translate all 81 tutorials from French to Vietnamese (hardcoded translations)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would be updated without saving to database'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes will be saved'))

        sections_updated = 0
        tutorials_updated = 0
        sections_missing = 0
        tutorials_missing = 0

        for section in TutorialSection.objects.all().order_by('order'):
            sec_data = TRANSLATIONS.get(section.order)
            if not sec_data:
                self.stdout.write(self.style.WARNING(
                    f'  No translation for section {section.order}: {section.title}'
                ))
                sections_missing += 1
                continue

            section.title_vi = sec_data['title_vi']
            if not dry_run:
                section.save(update_fields=['title_vi'])
            sections_updated += 1
            self.stdout.write(self.style.SUCCESS(
                f'  Section {section.order}: {section.title_fr} -> {sec_data["title_vi"]}'
            ))

            for tutorial in section.tutorials.all().order_by('number'):
                tut_data = sec_data.get('tutorials', {}).get(tutorial.number)
                if not tut_data:
                    self.stdout.write(self.style.WARNING(
                        f'    No translation for tutorial {section.order}.{tutorial.number}: {tutorial.title}'
                    ))
                    tutorials_missing += 1
                    continue

                tutorial.title_vi = tut_data['title_vi']
                tutorial.steps_vi = json.dumps(tut_data['steps_vi'], ensure_ascii=False)
                tutorial.tip_vi = tut_data.get('tip_vi', '')

                if not dry_run:
                    tutorial.save(update_fields=['title_vi', 'steps_vi', 'tip_vi'])

                tutorials_updated += 1
                self.stdout.write(f'    {section.order}.{tutorial.number}: {tut_data["title_vi"]}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Translation complete: {sections_updated} sections, {tutorials_updated} tutorials updated'
        ))
        if sections_missing or tutorials_missing:
            self.stdout.write(self.style.WARNING(
                f'Missing translations: {sections_missing} sections, {tutorials_missing} tutorials'
            ))
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes were saved'))
