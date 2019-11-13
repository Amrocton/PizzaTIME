import sys
import csv
import sqlite3
from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QWidget, QTableWidgetItem

cpassword = 'tetyazina'


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('pizzaicon.png'))
        uic.loadUi('mainwin.ui', self)
        self.clientbtn.clicked.connect(self.clienForm)
        self.cashbtn.clicked.connect(self.cashForm)

    def clienForm(self):
        self.client_form = ClientForm()
        self.client_form.show()

    def cashForm(self):
        global cpassword
        inpassword, btnpresd = QInputDialog.getText(self, 'Вход', 'Введите пароль от кассира')
        while cpassword != inpassword and btnpresd:
            inpassword, btnpresd = QInputDialog.getText(self, 'Вход', 'Неправильный пароль')
        if btnpresd:
            self.cashierFrom = CashierForm()
            self.cashierFrom.show()


class ClientForm(QWidget):
    def __init__(self):
        super().__init__()
        self.nameslist = []
        uic.loadUi('clientwin.ui', self)
        self.setWindowIcon(QIcon('pizzaicon.png'))
        self.clientlist = {}
        self.client = 1
        self.setMenu()
        self.menu.itemDoubleClicked.connect(self.showPizza)
        self.addbtn.clicked.connect(self.addToBasket)
        self.basketbtn.clicked.connect(self.showBasket)

    def setMenu(self):
        con = sqlite3.connect('pizzeria.db')
        cur = con.cursor()
        pizzas = cur.execute('''SELECT name, price FROM Menu''')
        for i, row in enumerate(list(pizzas)):
            self.menu.setRowCount(self.menu.rowCount() + 1)
            self.nameslist.append(row[0])
            for j, elem in enumerate(row):
                self.menu.setItem(i, j, QTableWidgetItem(str(elem)))
        self.menu.resizeColumnsToContents()
        con.close()

    def showPizza(self, item):
        pizza = item.text()
        if pizza in self.nameslist:
            con = sqlite3.connect('pizzeria.db')
            cur = con.cursor()
            imname = \
                cur.execute(f'''SELECT imname FROM Menu WHERE name LIKE '{pizza}' ''').fetchone()[0]
            con.close()
            self.pizzaim = PizzaImage(pizza, imname)
            self.pizzaim.show()

    def addToBasket(self):
        pizza = self.menu.selectedItems()
        if pizza:
            if pizza[0].text() in self.nameslist:
                count, check = QInputDialog.getInt(self, 'Количество пиццы',
                                                   'Сколько пиццы закажите?',
                                                   1, 1, 15, 1)
                if check:
                    con = sqlite3.connect('pizzeria.db')
                    cur = con.cursor()
                    price = cur.execute(
                        f'''SELECT price FROM Menu 
                            WHERE name LIKE '{pizza[0].text()}' ''').fetchone()
                    con.close()
                    if pizza[0].text() not in self.clientlist.keys():
                        self.clientlist[pizza[0].text()] = (count, price[0] * count)
                    else:
                        self.clientlist[pizza[0].text()] = (
                            self.clientlist[pizza[0].text()][0] + count,
                            price[0] * (self.clientlist[pizza[0].text()][0] + count))
                    self.totalpr.setText(
                        f'Итого: {sum(self.clientlist[lest][1] for lest in self.clientlist)}')

    def showBasket(self):
        self.basket = Basket(self, self.clientlist, self.nameslist)
        self.basket.show()


class Basket(QWidget):
    def __init__(self, client, clientlist, nameslist):
        super().__init__()
        uic.loadUi('basketwin.ui', self)
        self.setWindowIcon(QIcon('pizzaicon.png'))
        self.client = client
        self.clientlist = clientlist
        self.nameslist = nameslist
        self.setReciept()
        self.deletebtn.clicked.connect(self.deletePizza)
        self.orderbtn.clicked.connect(self.makeOrder)

    def setReciept(self, clear=False):
        self.receipt.setRowCount(0)
        if clear:
            self.receipt.clear()
            self.receipt.setHorizontalHeaderLabels(['Название', 'Кол-во', 'Общая цена'])
        if self.clientlist:
            lest = [[i, self.clientlist[i][0], self.clientlist[i][1]] for i in self.clientlist]
            for i, row in enumerate(lest):
                self.receipt.setRowCount(self.receipt.rowCount() + 1)
                for j, elem in enumerate(row):
                    self.receipt.setItem(i, j, QTableWidgetItem(str(elem)))
            self.receipt.resizeColumnsToContents()
            self.totalpr.setText(
                f'Итого: {sum(self.clientlist[lest][1] for lest in self.clientlist)}')

    def deletePizza(self):
        pizza = self.receipt.selectedItems()
        if pizza:
            if self.clientlist and pizza[0].text() in self.nameslist:
                count, check = QInputDialog.getInt(self, 'Удаление из корзины',
                                                   'Сколько пиццы убрать из корзины?',
                                                   1, 1, self.clientlist[pizza[0].text()][0], 1)
                if check:
                    con = sqlite3.connect('pizzeria.db')
                    cur = con.cursor()
                    price = cur.execute(
                        f'''SELECT price FROM Menu 
                        WHERE name LIKE '{pizza[0].text()}' ''').fetchone()
                    con.close()
                    check = False
                    if self.clientlist[pizza[0].text()][0] - count == 0:
                        del self.clientlist[pizza[0].text()]
                        self.totalpr.setText('Итого: 0')
                        self.client.totalpr.setText('Итого: 0')
                        check = True
                    else:
                        self.clientlist[pizza[0].text()] = (
                            self.clientlist[pizza[0].text()][0] - count,
                            price[0] * (self.clientlist[pizza[0].text()][0] - count))
                        self.totalpr.setText(
                            f'Итого: {sum(self.clientlist[lest][1] for lest in self.clientlist)}')
                        self.client.totalpr.setText(
                            f'Итого: {sum(self.clientlist[lest][1] for lest in self.clientlist)}')
                    self.setReciept(check)

    def makeOrder(self):
        with open('client.csv', 'w', encoding='utf8') as csvfile:
            writer = csv.writer(
                csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            lest = [tuple(map(str, [i, self.clientlist[i][0], self.clientlist[i][1]])) for i in self.clientlist]
            for row in lest:
                writer.writerow(row)


class PizzaImage(QWidget):
    def __init__(self, pizza, imname):
        super().__init__()
        uic.loadUi('pizzaimwin.ui', self)
        self.setWindowTitle(pizza)
        self.setWindowIcon(QIcon('pizzaicon.png'))
        self.setGeometry(0, 0, QPixmap(f'images\{imname}').width(),
                         QPixmap(f'images\{imname}').height())
        self.pizzaim.setPixmap(QPixmap(f'images\{imname}'))


class CashierForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setClientOrder()

    def setClientOrder(self):
        with open('client.csv', 'r', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';', quotechar='"')
            title = next(reader.copy())
            self.order.setColumnCount(len(title))
            self.order.setHorizontalHeaderLabels(title)
            self.order.setRowCount(0)
            for i, row in enumerate(reader):
                self.order.setRowCount(self.order.rowCount() + 1)
                for j, elem in enumerate(row):
                    self.order.setItem(i, j, QTableWidgetItem(elem))
        self.order.resizeColumnsToContents()

    def acceptOrder(self):
        with open('client.csv', 'w', encoding='utf8') as __:
            pass


app = QApplication(sys.argv)
ex = MainWindow()
ex.show()
sys.exit(app.exec())
