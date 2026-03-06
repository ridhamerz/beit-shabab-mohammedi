# حجوزات بيت الشباب - نسخة بسيطة 2025
# كل شخص = سرير واحد فقط

from datetime import datetime, timedelta
import os

# ------------------- البيانات الأساسية -------------------
rooms = {
    "ذكور": {
        "غرفة 01": {"total": 6, "booked": 0, "reservations": []},
        "غرفة 02": {"total": 6, "booked": 0, "reservations": []},
        "غرفة 03": {"total": 6, "booked": 0, "reservations": []},
        "غرفة 04": {"total": 6, "booked": 0, "reservations": []},
        "غرفة 05": {"total": 6, "booked": 0, "reservations": []},
        "مرقد ذكور 1": {"total": 3, "booked": 0, "reservations": []},
        "مرقد ذكور 2": {"total": 4, "booked": 0, "reservations": []},
    },
    "عائلي/إناث": {
        "غرفة 06": {"total": 3, "booked": 0, "reservations": []},
        "غرفة 07": {"total": 6, "booked": 0, "reservations": []},
        "غرفة 08": {"total": 6, "booked": 0, "reservations": []},
        "غرفة 09": {"total": 6, "booked": 0, "reservations": []},
        "مرقد إناث 1": {"total": 1, "booked": 0, "reservations": []},   # افتراضي 1 → صحح إذا لازم
        "مرقد إناث 2": {"total": 40, "booked": 0, "reservations": []},
    }
}

reservations = []  # قائمة عامة لكل الحجوزات

# ------------------- الدوال المساعدة -------------------
def calculate_free_beds():
    for gender in rooms:
        for room_name, data in rooms[gender].items():
            data["booked"] = len(data["reservations"])
            data["free"] = data["total"] - data["booked"]

def show_available_rooms():
    print("\n" + "="*60)
    print("          الغرف المتوفرة حالياً          ")
    print("="*60)
    for gender, room_dict in rooms.items():
        print(f"\n{ gender.upper() }")
        print("-"*50)
        print(f"{'الغرفة':<18} {'إجمالي الأسرة':<15} {'محجوز':<10} {'فارغ':<10}")
        print("-"*50)
        for room_name, data in room_dict.items():
            print(f"{room_name:<18} {data['total']:<15} {data['booked']:<10} {data['free']:<10}")
    print("="*60 + "\n")

def add_reservation():
    nom = input("الإسم: ").strip()
    prenom = input("اللقب: ").strip()
    gender = input("ذكر أم أنثى/عائلي؟ (ذكر / انثى): ").strip().lower()
    
    if gender.startswith("ذ"):
        section = "ذكور"
    else:
        section = "عائلي/إناث"
    
    show_available_rooms()
    room_choice = input(f"إختر اسم الغرفة اللي تبغي تحجز فيها (من {section}): ").strip()
    
    if section not in rooms or room_choice not in rooms[section]:
        print("الغرفة غير موجودة أو في جناح خاطئ!")
        return
    
    room = rooms[section][room_choice]
    if room["free"] <= 0:
        print("ما عندها أسرّة فارغة في هذي الغرفة!")
        return
    
    date_str = input("تاريخ بداية الحجز (مثال: 2025-03-15): ")
    days = int(input("عدد الأيام: "))
    
    try:
        start = datetime.strptime(date_str, "%Y-%m-%d")
        end = start + timedelta(days=days-1)
    except:
        print("تاريخ غير صحيح!")
        return
    
    # تسجيل الحجز
    reservation = {
        "nom": nom,
        "prenom": prenom,
        "room": room_choice,
        "section": section,
        "start": start,
        "end": end,
        "date_added": datetime.now()
    }
    
    room["reservations"].append(reservation)
    reservations.append(reservation)
    print(f"\nتم الحجز بنجاح لـ {nom} {prenom} في {room_choice} من {start.date()} إلى {end.date()}\n")

def show_all_reservations():
    if not reservations:
        print("ما عندكش حجوزات بعد.")
        return
    
    print("\n" + "="*80)
    print("              جميع الحجوزات              ")
    print("="*80)
    print(f"{'الإسم':<15} {'اللقب':<15} {'الغرفة':<18} {'بداية':<12} {'نهاية':<12}")
    print("-"*80)
    for r in sorted(reservations, key=lambda x: x["start"]):
        print(f"{r['nom']:<15} {r['prenom']:<15} {r['room']:<18} {r['start'].date():<12} {r['end'].date():<12}")
    print("="*80 + "\n")

# ------------------- القائمة الرئيسية -------------------
def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        calculate_free_beds()
        print("=== نظام حجوزات بيت الشباب ===")
        print("1. عرض الغرف المتوفرة")
        print("2. إضافة حجز جديد")
        print("3. عرض جميع الحجوزات")
        print("4. خروج")
        
        choice = input("\nإختر (1-4): ").strip()
        
        if choice == "1":
            show_available_rooms()
        elif choice == "2":
            add_reservation()
        elif choice == "3":
            show_all_reservations()
        elif choice == "4":
            print("شكرا على الاستخدام!")
            break
        else:
            print("خيار غير صحيح!")
        
        input("\nإضغط Enter للمتابعة...")

if __name__ == "__main__":
    main()
