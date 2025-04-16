from abc import ABC, abstractmethod
from datetime import datetime, timedelta, date
import uuid
import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QComboBox,
    QMessageBox,
    QHeaderView,
    QDateEdit,
    QDialog,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QPalette, QColor, QBrush

class Járat(ABC):
    def __init__(self, járatszám: str, célállomás: str, ár: int) -> None:
        self.járatszám = járatszám
        self.célállomás = célállomás
        self.ár = ár

    @abstractmethod
    def info(self) -> str:
        pass

    @abstractmethod
    def visszatérítés_számolás(self, repulés_dátuma: date) -> int:
        pass

class BelföldiJárat(Járat):
    def __init__(self, járatszám: str, célállomás: str) -> None:
        super().__init__(járatszám, célállomás, ár=10000)

    def info(self) -> str:
        return f"Belföldi: {self.járatszám} - {self.célállomás} - {self.ár} Ft"

    def visszatérítés_számolás(self, repulés_dátuma: date) -> int:
        days_before = (repulés_dátuma - date.today()).days
        if days_before > 14:
            return self.ár  
        elif days_before > 7:
            return int(self.ár * 0.8) 
        elif days_before > 3:
            return int(self.ár * 0.5)  
        return 0  

class NemzetköziJárat(Járat):
    def __init__(self, járatszám: str, célállomás: str) -> None:
        super().__init__(járatszám, célállomás, ár=50000)

    def info(self) -> str:
        return f"Nemzetközi: {self.járatszám} - {self.célállomás} - {self.ár} Ft"

    def visszatérítés_számolás(self, repulés_dátuma: date) -> int:
        days_before = (repulés_dátuma - date.today()).days
        if days_before > 30:
            return self.ár  
        elif days_before > 14:
            return int(self.ár * 0.7)  
        elif days_before > 7:
            return int(self.ár * 0.5)  
        return 0  


class Légitársaság:
    def __init__(self, név: str) -> None:
        self.név = név
        self.járatok = [
            BelföldiJárat("B101", "Budapest"),
            BelföldiJárat("B102", "Szeged"),
            NemzetköziJárat("N201", "London"),
        ]
        
class JegyFoglalás:
    def __init__(self, járat: Járat, repulés_dátuma: date) -> None:
        self.azonosító = str(uuid.uuid4())[:8]
        self.járat = járat
        self.repulés_dátuma = repulés_dátuma
        self.foglalás_dátuma = datetime.now()
        self.ár = járat.ár  # Explicit ár tárolása

    def info(self) -> str:
        return f"{self.azonosító} | {self.járat.célállomás} | Repülési dátum: {self.repulés_dátuma} | Foglalás ideje: {self.foglalás_dátuma.strftime('%Y-%m-%d %H:%M')} | Ár: {self.ár} Ft"

    def calculate_refund(self) -> int:
        return self.járat.visszatérítés_számolás(self.repulés_dátuma)

class BookingListDialog(QDialog):
    def __init__(self, bookings, parent=None):
        super().__init__(parent)
        self.bookings = bookings
        self.setWindowTitle("Foglalások listája")

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Célállomás", "Repülési dátum", "Ár", "Visszatérítés"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("QTableWidget::item:selected { background-color: #3399FF; }")

        self.frissit_tabla()

        self.torles_button = QPushButton("Foglalás lemondása")
        self.torles_button.clicked.connect(self.torles)

        self.bezar_button = QPushButton("Bezárás")
        self.bezar_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.torles_button)
        button_layout.addWidget(self.bezar_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setMinimumSize(800, 400)

    def frissit_tabla(self):
        self.table.setRowCount(len(self.bookings))
        for row, booking in enumerate(self.bookings):
            refund = booking.calculate_refund()
            refund_text = f"{refund} Ft" if refund > 0 else "Nincs visszatérítés"
            
            for col, text in enumerate([
                booking.azonosító,
                booking.járat.célállomás,
                str(booking.repulés_dátuma),
                f"{booking.ár} Ft",
                refund_text
            ]):
                item = QTableWidgetItem(text)
                item.setForeground(QBrush(Qt.white))
                

                if col == 4:
                    if refund == booking.ár:
                        item.setBackground(QBrush(QColor(0, 128, 0)))  # Green for full refund
                    elif refund > 0:
                        item.setBackground(QBrush(QColor(0, 100, 0)))  # Darker green for partial refund
                    else:
                        item.setBackground(QBrush(QColor(128, 0, 0)))  # Red for no refund
                
                self.table.setItem(row, col, item)

    def torles(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0 and selected_row < len(self.bookings):
            booking = self.bookings[selected_row]
            refund = booking.calculate_refund()
            

            if refund > 0:
                refund_message = f"\nVisszatérítés összege: {refund} Ft"
            else:
                refund_message = "\nNincs jogosultság visszatérítésre."
            
            reply = QMessageBox.question(
                self,
                "Megerősítés",
                f"Biztosan lemondja ezt a foglalást?\n{booking.info()}{refund_message}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            
            if reply == QMessageBox.Yes:
                del self.bookings[selected_row]
                self.frissit_tabla()
                message = "A foglalás sikeresen lemondva."
                if refund > 0:
                    message += f"\n{refund} Ft összeg visszatérítésre kerül."
                QMessageBox.information(self, "Sikeres lemondás", message)
        else:
            QMessageBox.warning(self, "Hiba", "Nincs kijelölt foglalás a lemondáshoz!")


class RepuloJegyApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.légitársaság = Légitársaság("MALÉV")
        self.foglalások = []
        self.utoljára_foglalt = None
        today = date.today()
        for i, járat in enumerate(self.légitársaság.járatok):
            for j in range(2):
                days = i * 2 + j
                repulés_dátuma = today + timedelta(days=days)
                self.foglalások.append(JegyFoglalás(járat, repulés_dátuma))
        self.setWindowTitle("Repülőjegy Foglalási Rendszer")
        self.setGeometry(100, 100, 800, 600)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)

        self.init_ui()

    def init_ui(self) -> None:
        self.title_label = QLabel("Repülőjegy Foglalási Rendszer")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        self.layout.addWidget(self.title_label)

        self.jarat_combo = QComboBox()
        self.jarat_combo.addItem("Válasszon járatot...", None)
        for járat in self.légitársaság.járatok:
            self.jarat_combo.addItem(járat.info(), járat)
        self.jarat_combo.setCurrentIndex(0)
        self.layout.addWidget(QLabel("Járat kiválasztása:"))
        self.layout.addWidget(self.jarat_combo)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate().addDays(1))
        self.date_edit.setMinimumDate(QDate.currentDate().addDays(1))
        self.layout.addWidget(QLabel("Repülési dátum:"))
        self.layout.addWidget(self.date_edit)


        self.policy_label = QLabel(
            "Visszatérítési szabályzat:\n"
            "Belföldi járatok: 100% 14 nap, 80% 7 nap, 50% 3 nap előtt\n"
            "Nemzetközi járatok: 100% 30 nap, 70% 14 nap, 50% 7 nap előtt"
        )
        self.policy_label.setStyleSheet("background-color: #333; padding: 10px;")
        self.layout.addWidget(self.policy_label)

        self.button_layout = QHBoxLayout()
        self.foglalas_button = QPushButton("Foglalás")
        self.foglalas_button.clicked.connect(self.foglalas)
        self.button_layout.addWidget(self.foglalas_button)

        self.listaz_button = QPushButton("Foglalások listázása")
        self.listaz_button.clicked.connect(self.listaz)
        self.button_layout.addWidget(self.listaz_button)

        self.layout.addLayout(self.button_layout)

        self.utoljara_foglalt_label = QLabel("Nincs foglalt jegy.")
        self.utoljara_foglalt_label.setAlignment(Qt.AlignCenter)
        self.utoljara_foglalt_label.setStyleSheet("background-color: #333; padding: 10px;")
        self.layout.addWidget(self.utoljara_foglalt_label)

        self.layout.addStretch()

    def listaz(self) -> None:
        dialog = BookingListDialog(self.foglalások, self)
        dialog.exec()

    def foglalas(self) -> None:
        járat = self.jarat_combo.currentData()
        if not járat:
            QMessageBox.warning(self, "Hiba", "Válasszon érvényes járatot!")
            return

        qdate = self.date_edit.date()
        repulés_dátuma = date(qdate.year(), qdate.month(), qdate.day())
        if repulés_dátuma <= date.today():
            QMessageBox.warning(self, "Hiba", "A repülési dátum nem lehet ma vagy a múltban!")
            return


        if any(f.járat.járatszám == járat.járatszám and f.repulés_dátuma == repulés_dátuma for f in self.foglalások):
            QMessageBox.warning(self, "Hiba", "Ez a járat már foglalt erre a dátumra!")
            return

        foglalás = JegyFoglalás(járat, repulés_dátuma)
        self.foglalások.append(foglalás)
        self.utoljára_foglalt = foglalás
        self.frissit_utoljara_foglalt_label()
        


        if isinstance(járat, BelföldiJárat):
            policy_info = (
                "\n\nVisszatérítési szabályzat:\n"
                "- 14 napnál korábbi lemondás: 100%\n"
                "- 7-14 nap közötti lemondás: 80%\n"
                "- 3-7 nap közötti lemondás: 50%\n"
                "- 3 napon belüli lemondás: 0%"
            )
        elif isinstance(járat, NemzetköziJárat):
            policy_info = (
                "\n\nVisszatérítési szabályzat:\n"
                "- 30 napnál korábbi lemondás: 100%\n"
                "- 14-30 nap közötti lemondás: 70%\n"
                "- 7-14 nap közötti lemondás: 50%\n"
                "- 7 napon belüli lemondás: 0%"
            )
        
        QMessageBox.information(
            self, 
            "Sikeres foglalás", 
            f"Sikeres foglalás:\n{foglalás.info()}\nÁr: {foglalás.ár} Ft{policy_info}"
        )

    def frissit_utoljara_foglalt_label(self) -> None:
        if self.utoljára_foglalt:
            self.utoljara_foglalt_label.setText(
                f"Utoljára foglalt jegy:\n{self.utoljára_foglalt.info()}"
            )
            self.utoljara_foglalt_label.setStyleSheet("background-color: #3399FF; color: white; padding: 10px;")
        else:
            self.utoljara_foglalt_label.setText("Nincs foglalt jegy.")
            self.utoljara_foglalt_label.setStyleSheet("background-color: #333; padding: 10px;")


if __name__ == "__main__":
    app = QApplication(sys.argv)


    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Highlight, QColor(85, 170, 255))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)

    window = RepuloJegyApp()
    window.show()
    sys.exit(app.exec())