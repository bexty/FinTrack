#в textField добавить кнопку выбора даты, на случай, когда нужно ввести не сегодняшнюю транзакцию
#в textField добавить кнопку Done, для прекращиения ввода на этапе цена + категория, чтобы не происходило запроса названия транзакции
#добавить режим просмотра периода дат
#добавить режим просмотра месяца не по категориям, а по транзакциям в порядке даты их добавления, mode L (List)



import sys, ui, dialogs, pickle, console, os, sqlite3

#print(sys.argv[1])

INITIALMODE = 'M' #режим, в котором стартует приложение по умолчанию, D = Date, M = Month, Y = Year, A = All time
FOLDERPATH = '/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/FinTrack/'
DB = 'test2.db'
MONTH = ('дурак', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec') #нулевой индекс как заглушка, т.к. sqlite и datePicker возвращает месяц в виде числа 1-12, а не 0-11

testTableData = [['qwerty', ['zero', 'one', 'two', 'three']],
                 ['abc', ['zero', 'one', 'two', 'three']]]



class MainLogic():
    def __init__(self):
        self.mode = INITIALMODE
        self.date = self.now()
        self.modeButton = ui.ButtonItem(title=self.mode, action=self.changeMode)
        self.settingsButton = ui.ButtonItem(title=' ⚙️ ', action=self.goToSettings)
        self.calendarButton = ui.ButtonItem(title=' 📆 ', action=self.selectDate)
        self.addButton = ui.ButtonItem(title=' ➕ ', action=self.addPurchase)
        self.searchButton = ui.ButtonItem(title=' 🔎 ', action=self.search)
        self.mainTable = Table( name='',
                                items=testTableData,
                                action=self.rowSelected,
                                editAction=self.rowDeleted,
                                rightButtonList=(self.addButton, self.searchButton),
                                leftButtonList=(self.modeButton, self.calendarButton, self.settingsButton))
        self.mainTableNameUpdate()
        self.mainTable.present()

    def now(self):
        connection = sqlite3.connect(FOLDERPATH+DB)
        db = connection.cursor()
        a = str(db.execute('SELECT datetime("now", "localtime")').fetchone()[0]) #формат строки '2021-01-27 16:10:45'
        connection.close()
        return  a

    def mainTableNameUpdate(self): #сюда еще добавить в выходную строку сумму за выбранный период, формат date = '2021-01-27 16:10:45'
        self.modeButton.title = self.mode
        if self.mode=='D':
            self.mainTable.name = (self.date[8:10]+'.'+self.date[5:7]+'.'+self.date[0:4])
        elif self.mode=='M':
            self.mainTable.name = (MONTH[int(self.date[5:7])]+' '+self.date[0:4])
        elif self.mode=='Y':
            self.mainTable.name = self.date[0:4]
        elif self.mode=='A':
            self.mainTable.name = 'All'
        else:
            print('MainLogic.mainTableNameUpdate() error, что-то у нас непредвиденный режим')

    def rowSelected(self, sender):
        sender.items[sender.selected_section][1].insert(sender.selected_row+1, 'lol') # +1 для вставки ниже выбранной строки
        sender.tableview.insert_rows([(sender.selected_row+1, sender.selected_section)])

    def rowDeleted(self, sender):
        pass

    def changeMode(self, sender):
        answer = dialogs.list_dialog(title='Period?', items=('Day', 'Month', 'Year', 'All time'), multiple=False)
        if answer == 'Day':
            self.mode = 'D'
        elif answer == 'Month':
            self.mode = 'M'
        elif answer == 'Year':
            self.mode = 'Y'
        elif answer == 'All time':
            self.mode='A'
        elif answer == None:
            pass
        else:
            print('changeMode() error, что-то у нас непредвиденный режим')
        self.mainTableNameUpdate()

    def selectDate(self, sender):
        d=DatePicker(name='Date?')
        d.present()
        d.waitModal()
        self.date = d.date
        self.mainTableNameUpdate()

    def goToSettings(self, sender):
        print('here I am in settings')
        txt = ui.TextField(flex='WH')
        self.view.add_subview(txt)

    def search(self, sender):
        print('searching')

    @ui.in_background
    def addPurchase(self, sender):
        date = self.date
        category = None
        name = None
        note = '' #пока не использую, планирую заполнять это поле при автоматическом добавлении покупки из iOS Shortcuts
        cost = None
        
        r = TextField()
        status = 'run'

        def cancel(sender):
            status = 'stop'
            r.close()
            print('cancel action')
        
        def selectDate(sender):
            print('select date action')

        def done(sender):
            print('done action')

        cancelButton = ui.ButtonItem(title='Cancel', action=cancel)
        calendarButton = ui.ButtonItem(title=' 📆 ', action=selectDate)
        doneButton = ui.ButtonItem(title='Done', action=done)

        #@ui.in_background
        def getCost():
            r.name = 'Сумма?'
            r.keyboard = ui.KEYBOARD_DECIMAL_PAD
            r.buttons = [['left', cancelButton], ['left', calendarButton]]
            x = r.present()
            #r.close()
            if x == '': #проверка на пустую строку из-за того, что если закрыть TextField() свайпом вниз, то возвращается пустая строка
                status = 'stop'
                return None
            else:
                return int(x)

        #@ui.in_background
        def getCategory(): 
            connection = sqlite3.connect(FOLDERPATH+DB)
            connection.row_factory = lambda cursor, row: row[0] #эта магия позволяет возвращать из db список, а не список кортежей, то есть возвращает нулевой элемент каждого кортежа
            db = connection.cursor()
            a = db.execute('SELECT name FROM categories ORDER BY id').fetchall()
            connection.close()

            category = dialogs.list_dialog(title='Категория?', items=a, multiple=False)
            if category == None:
                status = 'stop'
            return category

        #@ui.in_background
        def getName():
            r.name = 'Название?'
            r.keyboard = ui.KEYBOARD_DEFAULT
            r.buttons = [['left', cancelButton], ['left', calendarButton], ['right', doneButton]]
            x = r.present()
            if x == '': #проверка на пустую строку из-за того, что если закрыть TextField() свайпом вниз, то возвращается пустая строка
                status = 'stop'
                return None
            else:
                return x

        cost = getCost()
        r.close()
        if cost:
            category = getCategory()
            if category:
                name = getName()
                r.close()

        print(status)
        print(cost)
        print(category)
        print(name)
        print(date)

            
class TextField():
    def __init__(self):
        self.txt = ui.TextField(flex='WH')
        self.txt.autocorrection_type = True
        self.txt.keyboard_type = ui.KEYBOARD_DEFAULT
        #self.txt.action = self.act
        self.view = ui.View(background_color='white')
        self.view.add_subview(self.txt)

    #def act(self, sender):
        #print(sender)
        #sender.superview.close()
        
    def present(self):
        self.view.present(hide_close_button=True)
        self.txt.begin_editing()
        self.txt.wait_modal()
        #self.txt.superview.close()
        #self.view.wait_modal()
        #self.txt.close()
        #self.view.close()
        return self.txt.text

    def close(self):
        #self.txt.close()
        #self.view.close()
        pass

    def setName(self, name):
        self.view.name = name

    name = property(None, setName)

    def setText(self, text):
        self.txt.text = text

    text = property(None, setText)

    def setKeyboard(self, keyboard):
        self.txt.keyboard_type = keyboard

    keyboard = property(None, setKeyboard)

    def setAutocorrection(self, state):
        self.txt.autocorrection_type = state

    autocorrection = property(None, setAutocorrection)

    def setButtons(self, buttons): #buttons = [['left or rigth, button object], ]
        leftButtons = []
        rightButtons = []
        for i in buttons:
                if i[0] == 'left':
                    leftButtons.append(i[1])
                elif i[0] == 'right':
                    rightButtons.append(i[1])
        self.view.left_button_items = leftButtons
        self.view.right_button_items = rightButtons

    buttons = property(None, setButtons)


class DatePicker(): #выдает дату формата 2020-12-31 22:18:55
    def __init__(self, name='', mode=ui.DATE_PICKER_MODE_DATE):
        self.dp = ui.DatePicker()
        self.dp.mode=mode
        self.view = ui.View(name=name, background_color='white')
        self.view.add_subview(self.dp)

    def present(self):
        self.view.present(hide_close_button=False)

    def waitModal(self):
        self.dp.wait_modal()

    def get_date(self):
        a = str(self.dp.date)
        return (a[8:10]+'.'+a[5:7]+'.'+a[0:4]+' '+a[11:16]) #приводим дату к виду '31.12.2020 22:17', так с ней удобнее работать.

    date = property(get_date, None)


class FinTransaction():
    def __init__(self, transactionId=None, transactionDate=None, transactionFromDB=()):
        if transactionFromDB:
            self.id = int(transactionFromDB.id)
            self.name = str(transactionFromDB.name)
            self.category = str(transactionFromDB.category)
            self.cost = int(transactionFromDB.cost)
            self.date = str(transactionFromDB.date)
            self.note = str(transactionFromDB.note)
        else:
            '''self.id = int(transactionId)
            self.name = str()
            self.category = str()
            self.cost = int()
            self.date = str(transactionDate)
            self.note = str()'''
            self.name = Request(name='test request', selectDateAction=self.selectDateAction).value
            print(self.name)

    def ask(self):
        return None

    def selectDateAction(self, sender):
        print('date selection is working')


class Table():
    def __init__(self, name, items, action, leftButtonList=(), rightButtonList=(), editAction=None, moveEnable=False, deleteEnable=True):
        self.dataSource = MyListDataSource(items)
        self.dataSource.move_enabled = moveEnable
        self.dataSource.delete_enabled = deleteEnable
        #self.dataSource.accessory_action = accessoryAction
        self.dataSource.action = action
        self.dataSource.edit_action = editAction #не удается выключить эту функцию почему-то. Можно поставить None, тогда реального действия не будет, но в ui все равно останется возможность удаления свайпом
        self.table = ui.TableView(data_source=self.dataSource, delegate=self.dataSource, flex='WH')
        self.view = ui.View(name=name, background_color='white')
        self.view.right_button_items = rightButtonList
        self.view.left_button_items = leftButtonList
        self.view.add_subview(self.table)

    def present(self):
        self.view.present(hide_close_button=True)

    def close(self):
        self.view.close()

    def get_items(self):
        a =[]
        for x in self.dataSource.items:
            a.append(x['title'])
        return a

    def set_items(self, items):
        self.dataSource.items = self.listToDict(items, self.dataSource.accessory_action)

    items = property(get_items, set_items)

    def set_name(self, name):
        self.view.name = name

    name = property(None, set_name)


class MyListDataSource ():
    #переопределяем часть методов от родительского класса, т. к. в нем нет поддержки секций для табицы.
    #items = [['section0_name', ['row0', 'row1', 'row2']], ['section1_name', [{},{},{}]]]
    #row = items[section_index][1][row_index]
    #section_name = items[section_index][0]
    def __init__(self, items):
        self.tableview = None
        self.reload_disabled = False
        self.delete_enabled = True
        self.move_enabled = False

        self.action = None
        self.edit_action = None
        self.accessory_action = None

        self.tapped_accessory_row = -1
        self.selected_row = -1
        self.tapped_accessory_section = -1
        self.selected_section = -1

        self.items = items

        self.text_color = None
        self.highlight_color = None
        self.font = None
        self.number_of_lines = 1

    def reload(self):
        if self.tableview and not self.reload_disabled:
            self.tableview.reload()

    def tableview_cell_for_row(self, tv, section, row):
        self.tableview = tv
        item = self.items[section][1][row]
        cell = ui.TableViewCell()
        cell.text_label.number_of_lines = self.number_of_lines
        if isinstance(item, dict):
            cell.text_label.text = item.get('title', '')
            img = item.get('image', None)
            if img:
                if isinstance(img, basestring):
                    cell.image_view.image = Image.named(img)
                elif isinstance(img, Image):
                    cell.image_view.image = img
            accessory = item.get('accessory_type', 'none')
            cell.accessory_type = accessory
        else:
            cell.text_label.text = str(item)
        if self.text_color:
            cell.text_label.text_color = self.text_color
        if self.highlight_color:
            bg_view = View(background_color=self.highlight_color)
            cell.selected_background_view = bg_view
        if self.font:
            cell.text_label.font = self.font
        return cell

    def tableview_number_of_sections(self, tv):
        self.tableview = tv
        return len(self.items)

    def tableview_number_of_rows(self, tv, section):
        return len(self.items[section][1])

    def tableview_can_delete(self, tv, section, row):
        return self.delete_enabled

    def tableview_can_move(self, tv, section, row):
        return self.move_enabled

    def tableview_title_for_header(self, tv, section):
        return self.items[section][0]

    def tableview_accessory_button_tapped(self, tv, section, row):
        self.tapped_accessory_row = row
        self.tapped_accessory_section = section
        if self.accessory_action:
            self.accessory_action(self)

    def tableview_did_select(self, tv, section, row):
        self.selected_row = row
        self.selected_section = section
        if self.action:
            self.action(self)

    def tableview_did_deselect(self, tv, section, row):
        pass

    def tableview_title_for_delete_button(self, tv, section, row):
        return 'Delete'

    def tableview_move_row(self, tv, from_section, from_row, to_section, to_row):
        pass

    def tableview_delete(self, tv, section, row):
        self.reload_disabled = True
        del self.items[section][1][row]
        self.reload_disabled = False
        tv.delete_rows((section, row))
        if self.edit_action:
            self.edit_action(self)


class FinanceCollection(): #пустая заготовка на случай, если файла не окажется или он будет пустой. Если же файл уже есть - то грузимся с него в MainLogic
    def __init__(self):
        self.category = ['1. Продукты', '2. Анка', '3. Саша', '4. Фастфуд', '5. Развлечения', '6. Бытовая химия',
        '7. Здоровье', '8.Бензин', '9. Машина', '10. Связь',  '11. Жилье',  '12. Хозяйство',
        '13. Подарки', '14. Другое', '15. Обед на работе', '16. Одежда', '17. Проезд', '18. Стрижка']
        self.data = []

    def ask(self):
        pass


class Transaction():
    def __init__(self):
        pass


main = MainLogic()
#a = FinTransaction()

