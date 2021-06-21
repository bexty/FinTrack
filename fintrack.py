import sys, ui, dialogs, pickle, os, sqlite3, threading, random, time

DB = './fintrack text primary key.db'

TABLECELLLENGHT = 30 #количесвто символов, которое помещается в одной строке таблицы (когда категория открыта), зависит от размера шрифта SMALLFONT
SMALLFONT = ('<system>', 14) #размер шрифта в таблице в открытой категории (он меньше чем шрифт самой категории)
CURRENCYSYMBOL =  ' ₽'
INITIALMODE = 'M' #режим, в котором стартует приложение по умолчанию, D = Date, M = Month, Y = Year, A = All time
MONTH = ('дурак',
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December') #нулевой индекс как заглушка, т.к. sqlite и datePicker возвращает месяц в виде числа 1-12, а не 0-11

CALENDAR = 'calendar36.png'
PERIOD = 'period36.png'
ADD = 'plus36.png'
SEARCH = 'search36.png'
SETTINGS = 'settings36.png'

CHANDEPERIODWIDTH = 150
CHANDEPERIODHEIGHT = 300

DPHEIGHT = 180
DPDONEBUTTONHEIGHT = 72
DPDONEBUTTONINTRANSACTIONHEIGHT = 36
CANCELBUTTONHEIGHT = SMALLCALENDARBUTTONHEIGHT = ENTERBUTTONHEIGHT = DONEBUTTONHEIGHT = TEXTFIELDHEIGHT = 36

class MyListDataSource ():
    #переопределяем часть методов от родительского класса, т. к. в нем нет поддержки секций для табицы.
    #items = [{'sectionName':'', 'rows':[{'rowName':'', 'rowSum':''}, {'rowName':'', 'rowSum':''}, {'rowName':'', 'rowSum':''}]},
    #         {'sectionName':'', 'rows':[{'rowName':'', 'rowSum':''}, {'rowName':'', 'rowSum':''}, {'rowName':'', 'rowSum':''}]},
    #         {'sectionName':'', 'rows':[{'rowName':'', 'rowSum':''}, {'rowName':'', 'rowSum':''}, {'rowName':'', 'rowSum':''}]}]
    
    #rowName может быть простой строкой, а может быть списком словарей, смотри документацию на ui.ListDataSource
    def __init__(self, items, action=None, editAction=None, accessoryAction=None, deleteEnabled=True, moveEnabled=False):
        self.tableview = None
        self.reload_disabled = False
        self.delete_enabled = deleteEnabled
        self.move_enabled = moveEnabled

        self.action = action
        self.edit_action = editAction
        self.accessory_action = accessoryAction

        self.tapped_accessory_row = -1
        self.selected_row = -1
        self.tapped_accessory_section = -1
        self.selected_section = -1

        self.items = items

        self.text_color = None
        self.highlight_color = None
        self.font = None #('<system>', 12)
        self.number_of_lines = 1

    def reload(self):
        if self.tableview and not self.reload_disabled:
            self.tableview.reload()

    def tableview_cell_for_row(self, tv, section, row):
        self.tableview = tv
        item1 = self.items[section]['rows'][row]['rowName'] #rowName
        item2 = self.items[section]['rows'][row]['rowSum'] #rowSum
        cell = ui.TableViewCell(style='value1')
        cell.text_label.number_of_lines = self.number_of_lines
        cell.detail_text_label.text = str(item2)
        if isinstance(item1, dict):
            cell.text_label.text = item1.get('title', '')
            img = item1.get('image', None)
            if img:
                if isinstance(img, basestring):
                    cell.image_view.image = Image.named(img)
                elif isinstance(img, Image):
                    cell.image_view.image = img
            accessory = item1.get('accessory_type', 'none')
            cell.accessory_type = accessory
        else:
            cell.text_label.text = str(item1)
        if self.text_color:
            cell.text_label.text_color = self.text_color
        if self.highlight_color:
            bg_view = View(background_color=self.highlight_color)
            cell.selected_background_view = bg_view
        if self.font:
            cell.text_label.font = self.font
        if self.items[section]['sectionName'] != '':
            cell.text_label.font = SMALLFONT
            cell.detail_text_label.font = SMALLFONT
            cell.accessory_type = 'detail_button'
        return cell

    def tableview_number_of_sections(self, tv):
        self.tableview = tv
        return len(self.items)

    def tableview_number_of_rows(self, tv, section):
        return len(self.items[section]['rows'])

    def tableview_can_delete(self, tv, section, row):
        return self.delete_enabled

    def tableview_can_move(self, tv, section, row):
        return self.move_enabled

    def tableview_title_for_header(self, tv, section):
        return self.items[section]['sectionName']

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
        return ('Delete')

    def tableview_move_row(self, tv, from_section, from_row, to_section, to_row):
        pass

    def tableview_delete(self, tv, section, row):
        self.reload_disabled = True
        del self.items[section][1][row]
        self.reload_disabled = False
        tv.delete_rows((section, row))
        if self.edit_action:
            self.edit_action(self)

class MyView(ui.View):
    def __init__(self, name, flex, background_color):
        self.name = name
        self.flex = flex
        self.background_color = background_color

    def keyboard_frame_will_change(self, frame):
        global keyboardFrame
        keyboardFrame = ui.convert_rect(frame, to_view=self)

    def will_close(self):
        pass
    
    def layout(self):
        viewsResize()

class Transaction():
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

def cur(price, mode='rough'):
    if price == None:
        return '0₽'
    elif mode == 'rough':
        return (format(price, ',.0f').replace(',', '  ')+CURRENCYSYMBOL)
    elif mode == 'precisely':
        return (format(price, ',.2f').replace(',', '  ')+CURRENCYSYMBOL)
    else:
        raise ValueError('mode: несоответствующее значение')

def myRandom():
    return str(random.randint(0, 9999))

def createDb():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    
    cur.execute('''CREATE TABLE IF NOT EXISTS purchases(
                                id TEXT PRIMARY KEY,
                                name TEXT,
                                category TEXT,
                                price REAL,
                                date TEXT,
                                note TEXT)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS categories(
                                id INT PRIMARY KEY,
                                name TEXT)''')

    testDataCategories = [(0, 'Продукты'),
                        (1, 'Хозяйство'),
                        (2, 'Бытовая химия'),
                        (3, 'Анка'),
                        (4, 'Машина'),
                        (5, 'Фастфуд'),
                        (6, 'Бензин'),
                        (7, 'Долги'),
                        (8, 'Другое'),
                        (9, 'Жилье'),
                        (10, 'Здоровье'),
                        (11, 'Канцелярия'),
                        (12, 'Обед на работе'),
                        (13, 'Одежда'),
                        (14, 'Подарки'),
                        (15, 'Проезд'),
                        (16, 'Развлечения'),
                        (17, 'Саша'),
                        (18, 'Связь'),
                        (19, 'Списание'),
                        (20, 'Стрижка')]
    
    cur.executemany('INSERT INTO categories VALUES(?, ?)', testDataCategories)
    conn.commit()
    conn.close()

def getTheme():
    return ui.get_ui_style()

def viewsResize():
    periodButton.center = (periodButton.superview.width*0.1,
        (periodButton.superview.height-(periodButton.height/2)))
    calendarButton.center = (calendarButton.superview.width*0.3,
        (calendarButton.superview.height-(calendarButton.height/2)))
    settingsButton.center = (settingsButton.superview.width*0.5,
        (settingsButton.superview.height-(settingsButton.height/2)))
    searchButton.center = (searchButton.superview.width*0.7,
        (searchButton.superview.height-(searchButton.height/2)))
    addButton.center = (addButton.superview.width*0.9,
        (addButton.superview.height-(addButton.height/2)))
    table.width = table.superview.width
    table.height = (table.superview.height-periodButton.height)
    table.center = (table.superview.width/2,
        (table.superview.height-periodButton.height-(table.height/2)))

def now():
    connection = sqlite3.connect(DB)
    db = connection.cursor()
    now = db.execute('SELECT datetime("now", "localtime")').fetchone()[0]
    connection.close()
    return str(now)

def tableUpdate():
    def getNameForView():
        if mode == 'D':
            maskAndDate = ('%Y-%m-%d', date[0:10])
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            total = db.execute('SELECT sum(price) FROM purchases WHERE strftime(?, date) = ?', maskAndDate).fetchone()[0]
            connection.close()
            return (date[8:10]+'.'+date[5:7]+'.'+date[0:4]+' ('+cur(total)+')')
        elif mode == 'M':
            maskAndDate = ('%Y-%m', date[0:7])
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            total = db.execute('SELECT sum(price) FROM purchases WHERE strftime(?, date) = ?', maskAndDate).fetchone()[0]
            connection.close()
            return (MONTH[int(date[5:7])]+' '+date[0:4]+' ('+cur(total)+')')
        elif mode == 'Y':
            maskAndDate = ('%Y', date[0:4])
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            total = db.execute('SELECT sum(price) FROM purchases WHERE strftime(?, date) = ?', maskAndDate).fetchone()[0]
            connection.close()
            return (date[0:4]+' ('+cur(total)+')')
        elif mode == 'P':
            maskAndDate = ('%Y-%m-%d', date[0:10], endOfPeriodDate[0:10])
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            total = db.execute('SELECT sum(price) FROM purchases WHERE strftime(?, date) BETWEEN ? AND ?', maskAndDate).fetchone()[0]
            connection.close()
            return (date[8:10]+'.'+date[5:7]+'.'+date[2:4]+' - '+endOfPeriodDate[8:10]+'.'+endOfPeriodDate[5:7]+'.'+endOfPeriodDate[2:4]+' ('+cur(total)+')')
        elif mode == 'All':
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            total = db.execute('SELECT sum(price) FROM purchases').fetchone()[0]
            connection.close()
            return ('All'+' ('+cur(total)+')')
        else:
            raise ValueError('Несоответствующее значение')

    def getItemsForTable():
        if mode == 'D':
            maskAndDate = ('%Y-%m-%d', date[0:10])
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            result =[]
            for row in db.execute('SELECT category, sum(price) FROM purchases WHERE strftime(?, date) = ? GROUP BY category ORDER BY sum(price) DESC', maskAndDate):
                result.append({'sectionName':'', 'rows':[{'rowName':str(row[0]), 'rowSum':cur(row[1])}]})
            connection.close()
            return result
        elif mode == 'M':
            maskAndDate = ('%Y-%m', date[0:7])
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            result =[]
            for row in db.execute('SELECT category, sum(price) FROM purchases WHERE strftime(?, date) = ? GROUP BY category ORDER BY sum(price) DESC', maskAndDate):
                result.append({'sectionName':'', 'rows':[{'rowName':str(row[0]), 'rowSum':cur(row[1])}]})
            connection.close()
            return result
        elif mode == 'Y':
            maskAndDate = ('%Y', date[0:4])
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            result =[]
            for row in db.execute('SELECT category, sum(price) FROM purchases WHERE strftime(?, date) = ? GROUP BY category ORDER BY sum(price) DESC', maskAndDate):
                result.append({'sectionName':'', 'rows':[{'rowName':str(row[0]), 'rowSum':cur(row[1])}]})
            connection.close()
            return result
        elif mode == 'P':
            maskAndDate = ('%Y-%m-%d', date[0:10], endOfPeriodDate[0:10])
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            result =[]
            for row in db.execute('SELECT category, sum(price) FROM purchases WHERE strftime(?, date) BETWEEN ? AND ? GROUP BY category ORDER BY sum(price) DESC', maskAndDate):
                result.append({'sectionName':'', 'rows':[{'rowName':str(row[0]), 'rowSum':cur(row[1])}]})
            connection.close()
            return result
        elif mode == 'All':
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            result =[]
            for row in db.execute('SELECT category, sum(price) FROM purchases GROUP BY category ORDER BY sum(price) DESC'):
                result.append({'sectionName':'', 'rows':[{'rowName':str(row[0]), 'rowSum':cur(row[1])}]})
            connection.close()
            return result
        else:
            raise ValueError('Несоответствующее значение')

    view.name = getNameForView()
    dataSource.items = getItemsForTable()
    table.reload()

def rowSelected(sender): #sender - MyListDataSource object
    #sender.items[sender.selected_section][1].insert(sender.selected_row+1, 'lol') # +1 для вставки ниже выбранной строки
    #sender.tableview.insert_rows([(sender.selected_row+1, sender.selected_section)])
    #result = []
    rowsToInsert = []

    category = sender.items[sender.selected_section]['rows'][sender.selected_row]['rowName']
    sender.items[sender.selected_section]['sectionName'] = category
    sender.items[sender.selected_section]['rows'][sender.selected_row]['rowName'] = 'Total:'
    sender.tableview.reload()
    
    if mode == 'D':
        maskDateCategory = ('%Y-%m-%d', date[0:10], category)
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        for index, row in enumerate(db.execute('SELECT date(date), name, price FROM purchases WHERE strftime(?, date) = ? AND category = ? ORDER BY date DESC', maskDateCategory)):
            sender.items[sender.selected_section]['rows'].append({'rowName':str(row[0]+' '+str(row[1])), 'rowSum':cur(row[2])})
            rowsToInsert.append((index+1, sender.selected_section)) #+1 потому что 0 строка - это Total:
            pass
        connection.close()
    elif mode == 'M':
        maskDateCategory = ('%Y-%m', date[0:7], category)
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        for row in db.execute('SELECT date(date), name, price FROM purchases WHERE strftime(?, date) = ? AND category = ? ORDER BY date DESC', maskDateCategory):
            result.append({'dateAndName':str(row[0]+' '+str(row[1])), 'price':cur(row[2])})
        connection.close()
    elif mode == 'Y':
        maskAndDate = ('%Y', date[0:4])
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        for row in db.execute('SELECT category, sum(price) FROM purchases WHERE strftime(?, date) = ? GROUP BY category ORDER BY sum(price) DESC', maskAndDate):
            result.append({'sectionName':'', 'rows':[{'rowName':str(row[0]), 'rowSum':cur(row[1])}]})
        connection.close()
        return result
    elif mode == 'P':
        maskAndDate = ('%Y-%m-%d', date[0:10], endOfPeriodDate[0:10])
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        for row in db.execute('SELECT category, sum(price) FROM purchases WHERE strftime(?, date) BETWEEN ? AND ? GROUP BY category ORDER BY sum(price) DESC', maskAndDate):
            result.append({'sectionName':'', 'rows':[{'rowName':str(row[0]), 'rowSum':cur(row[1])}]})
        connection.close()
        return result
    elif mode == 'All':
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        for row in db.execute('SELECT category, sum(price) FROM purchases GROUP BY category ORDER BY sum(price) DESC'):
            result.append({'sectionName':'', 'rows':[{'rowName':str(row[0]), 'rowSum':cur(row[1])}]})
        connection.close()
        return result
    else:
        raise ValueError('Несоответствующее значение')
    
    #sender.items[sender.selected_section]['rows'] = result
    sender.tableview.insert_rows(rowsToInsert)

def rowDeleted(sender):
    pass

def accessoryTaped(sender):
    pass

def changePeriod(sender):
    @ui.in_background
    def rowSelected(sender):
        global mode
        global date
        global endOfPeriodDate

        if sender.items[sender.selected_row] == 'День':
            mode = 'D'
        elif sender.items[sender.selected_row] == 'Месяц':
            mode = 'M'
        elif sender.items[sender.selected_row] == 'Год':
            mode = 'Y'
        elif sender.items[sender.selected_row] == 'Период':
            mode = 'P'
            event = threading.Event() #флаг для ожидания пользовательского ввода в datePicker'ах, запускается в отдельном потоке
        
            def selectPeriodDone(sender):
                event.set() #снимаю флаг ожидания ответа пользователя в selectPeriod()
            
            t.touch_enabled = False

            fromDate = ui.DatePicker(name='From?',
                mode=ui.DATE_PICKER_MODE_DATE,
                background_color='white',
                border_color='black',
                border_width=2,
                corner_radius=5,
                alpha = 0.0)
            toDate = ui.DatePicker(name='To?',
                mode=ui.DATE_PICKER_MODE_DATE,
                background_color='white',
                border_color='black',
                border_width=2,
                corner_radius=5,
                alpha = 0.0)
            dDoneButton = ui.Button(title='Done',
                font=('<system-bold>', 20),
                action=selectPeriodDone,
                background_color='ceced2',
                border_width=1,
                border_color='white',
                corner_radius=5,
                alpha = 0.0)

            view.add_subview(fromDate)
            view.add_subview(toDate)
            view.add_subview(dDoneButton)

            dDoneButton.width = dDoneButton.superview.width
            dDoneButton.height = DPDONEBUTTONHEIGHT
            dDoneButton.center = (dDoneButton.superview.width/2,
                (dDoneButton.superview.height-dDoneButton.height/2))
            toDate.width = toDate.superview.width
            toDate.height = DPHEIGHT
            toDate.center = (toDate.superview.width/2,
                (dDoneButton.frame[1]-toDate.height/2))
            fromDate.width = fromDate.superview.width
            fromDate.height = DPHEIGHT
            fromDate.center = (fromDate.superview.width/2,
                (toDate.frame[1]-fromDate.height/2))
            
            dDoneButton.alpha = 1.0
            toDate.alpha = 1.0
            fromDate.alpha = 1.0

            event.clear() #ставим флаг ожидания ответа от пользователя, снимается он в selectPeriodDone()

            event.wait() #ожидаем пользовательского ввода, ждем до снятия флага, снимается он в selectPeriodDone()
            
            date = str(fromDate.date)
            endOfPeriodDate = str(toDate.date)

            dDoneButton.alpha = 0.0
            toDate.alpha = 0.0
            fromDate.alpha = 0.0

            view.remove_subview(dDoneButton)
            view.remove_subview(toDate)
            view.remove_subview(fromDate)
        elif sender.items[sender.selected_row] == 'Все время':
            mode = 'All'
        else:
            raise ValueError('Несоответствующее значение')

        tableUpdate()

        def hide():
            t.alpha = 0.0
            periodButton.enabled = True
            calendarButton.enabled = True
            settingsButton.enabled = True
            searchButton.enabled = True
            addButton.enabled = True
            table.touch_enabled = True
            table.alpha = 1.0

        def exit():
            view.remove_subview(t)
        
        ui.animate(hide, completion=exit)

    lds = ui.ListDataSource(items=('День',
        'Месяц',
        'Год',
        'Период',
        'Все время'))
    lds.action = rowSelected    
    t = ui.TableView(data_source=lds,
        delegate = lds)
    view.add_subview(t)
    t.border_width = 2
    t.corner_radius = 5
    t.width = CHANDEPERIODWIDTH
    t.height = CHANDEPERIODHEIGHT
    t.size_to_fit() #выставляет только высоту почему-то
    t.center = (t.width/2, t.superview.height - periodButton.height - t.height/2)
    t.alpha = 0.0
    #t.hidden = False
    
    def present():
        periodButton.enabled = False
        calendarButton.enabled = False
        settingsButton.enabled = False
        searchButton.enabled = False
        addButton.enabled = False
        table.touch_enabled = False
        table.alpha = 0.5
        t.alpha = 1.0
    
    ui.animate(present)

def selectDate(sender):
    def selectDateDone(sender):
        global date
        
        date = str(d.date)
        
        def hide():
            d.alpha = 0.0
            dDoneButton.alpha = 0.0
            periodButton.enabled = True
            calendarButton.enabled = True
            settingsButton.enabled = True
            searchButton.enabled = True
            addButton.enabled = True
            table.touch_enabled = True
            table.alpha = 1.0

        def exit():
            view.remove_subview(d)
            view.remove_subview(dDoneButton)
            tableUpdate()            

        ui.animate(hide, completion=exit)

    if mode == 'P':
        pass
    else:
        d = ui.DatePicker(name='Дата?',
            mode=ui.DATE_PICKER_MODE_DATE,
            background_color='white',
            border_color='black',
            border_width=2,
            corner_radius=5,
            alpha = 0.0)
        dDoneButton = ui.Button(title='Done',
            font=('<system-bold>', 20),
            action=selectDateDone,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            alpha = 0.0)

        view.add_subview(d)
        view.add_subview(dDoneButton)

        dDoneButton.width = dDoneButton.superview.width
        dDoneButton.height = DPDONEBUTTONHEIGHT
        dDoneButton.center = (dDoneButton.superview.width/2,
            (dDoneButton.superview.height-dDoneButton.height/2))
        d.width = d.superview.width
        d.height = DPHEIGHT
        d.center = (d.superview.width/2,
            (dDoneButton.frame[1]-d.height/2))
        
        def present():
            periodButton.enabled = False
            calendarButton.enabled = False
            settingsButton.enabled = False
            searchButton.enabled = False
            addButton.enabled = False
            table.touch_enabled = False
            table.alpha = 0.5
            dDoneButton.alpha = 1.0
            d.alpha = 1.0

        ui.animate(present)

@ui.in_background
def addTransaction(sender):
    global date
    #global view

    status = 'run' #run - спрашиваем все по очереди и записываем в БД, если заполнены обязательные поля. done - пропускаем необязательные поля (name). stop - останавливаем опрос, не записываем в бд
    doneButtonState = None    
    date = now()    
    event = threading.Event() #флаг для ожидания пользовательского ввода в addTransaction, которая запускается в отдельном потоке
    
    a = {'id':None, 'name':None, 'category':None,'price':None, 'date':None, 'note':None}

    periodButton.enabled = False
    calendarButton.enabled = False
    settingsButton.enabled = False
    searchButton.enabled = False
    addButton.enabled = False
    table.touch_enabled = False
    table.alpha = 0.5

    class MyTextFieldDelegate ():
        '''def textfield_should_begin_editing(self, textfield):
            return True

        def textfield_did_begin_editing(self, textfield):
            pass

        def textfield_did_end_editing(self, textfield):
            pass

        def textfield_should_return(self, textfield):
            textfield.end_editing()
            return True

        def textfield_should_change(self, textfield, range, replacement):
            return True'''

        def textfield_did_change(self, textfield):
            if textfield.text != '':
                enterButton.enabled = True 
                doneButton.enabled = True
            else:
                if textfield.placeholder == 'Цена?':
                    enterButton.enabled = False
                    doneButton.enabled = False
                elif textfield.placeholder == 'Имя?':
                    enterButton.enabled = False

    def ViewsResize():
        global keyboardFrame

        if keyboardFrame == (0.00, 0.00, 0.00, 0.00):
            def hide():
                cancelButton.alpha = 0.0
                localCalendarButton.alpha = 0.0
                enterButton.alpha = 0.0
                doneButton.alpha = 0.0
                textField.alpha = 0.0
                dpDoneButton.alpha = 0.0
                dp.alpha = 0.0
            ui.animate(hide)

        else:
            cancelButton.height = CANCELBUTTONHEIGHT
            cancelButton.width = cancelButton.superview.width/8
            cancelButton.center = (cancelButton.superview.width/16,
                (keyboardFrame[1] - (cancelButton.height/2)))

            localCalendarButton.height = SMALLCALENDARBUTTONHEIGHT
            localCalendarButton.width = localCalendarButton.superview.width/8
            localCalendarButton.center = (localCalendarButton.superview.width*0.1875,
                (keyboardFrame[1] - (calendarButton.height/2)))

            enterButton.height = ENTERBUTTONHEIGHT
            enterButton.width = enterButton.superview.width*0.5
            enterButton.center = (enterButton.superview.width*0.5,
                (keyboardFrame[1] - (enterButton.height/2)))

            doneButton.height = DONEBUTTONHEIGHT
            doneButton.width = doneButton.superview.width*0.25
            doneButton.center = (doneButton.superview.width*0.875,
                (keyboardFrame[1] - (doneButton.height/2)))

            textField.height = TEXTFIELDHEIGHT
            textField.width = textField.superview.width
            textField.center = (textField.superview.width//2,
                (keyboardFrame[1]-textField.height/2-enterButton.height))
            
            dpDoneButton.width = dpDoneButton.superview.width
            dpDoneButton.height = DPDONEBUTTONINTRANSACTIONHEIGHT
            dpDoneButton.center = (dpDoneButton.superview.width/2,
                (textField.frame[1]-dpDoneButton.height/2))

            dp.width = dp.superview.width
            dp.height = DPHEIGHT
            dp.center = (dp.superview.width/2,
                (dpDoneButton.frame[1]-dp.height/2))

            def present():
                cancelButton.alpha = 1.0
                localCalendarButton.alpha = 1.0
                enterButton.alpha = 1.0
                doneButton.alpha = 1.0
                textField.alpha = 1.0

            ui.animate(present)

    def dpDone(sender):
        global date
        nonlocal doneButtonState

        date = str(dp.date)
        localCalendarButton.enabled = True
        enterButton.enabled = True
        doneButton.enabled = doneButtonState
        def hide():
            dp.alpha = 0.0
            dpDoneButton.alpha = 0.0
        ui.animate(hide)

    def done(sender):
        nonlocal status
        status = 'done'
        enter(None)

    def selectDate(sender):
        nonlocal doneButtonState

        doneButtonState = doneButton.enabled
        localCalendarButton.enabled = False
        enterButton.enabled = False
        doneButton.enabled = False
        def present():
            dpDoneButton.alpha = 1.0
            dp.alpha = 1.0
        ui.animate(present)

    def enter(sender):
        event.set() #снимаю флаг ожидания ответа пользователя в addTransaction()

    def cancel(sender):
        nonlocal status
        status = 'stop'
        enter(None)

    def getPrice():
        nonlocal status
        if status == 'run':
            event.clear() #ставим флаг ожидания ответа от пользователя, снимается он в enter() по нажатию кнопки Enter
            textField.text=''
            textField.placeholder = 'Цена?'
            textField.keyboard_type = ui.KEYBOARD_DECIMAL_PAD
            textField.begin_editing()
            ViewsResize() #в зависимости от keyboardFrame показываем или скрываем элементы на экране
            event.wait() #ожидаем пользовательского ввода, ждем до снятия флага, снимается он в enter() по нажатию кнопки Enter
            textField.end_editing()
            ViewsResize() #в зависимости от keyboardFrame показываем или скрываем элементы на экране
            enterButton.enabled = False
            if textField.text != '':
                price = textField.text.replace(',','.') #чтобы десятичные дроби нормально понимал
                return float(price)
            else:
                status = 'stop'
                return None
        else:
            return None

    def getCategory():
        nonlocal status
        if status == 'run':
            connection = sqlite3.connect(DB)
            connection.row_factory = lambda cursor, row: row[0] #эта магия позволяет возвращать из db список, а не список кортежей, то есть возвращает нулевой элемент каждого кортежа
            db = connection.cursor()
            categories = db.execute('SELECT name FROM categories ORDER BY id').fetchall()
            connection.close()

            selectedCategory = dialogs.list_dialog(title='Категория?', items=categories, multiple=False)

            if selectedCategory == None:
                status = 'stop'
                return None
            else:
                return selectedCategory
        else:
            return None

    def getName():
        nonlocal status
        if status == 'run':
            event.clear()
            textField.text=''
            textField.placeholder = 'Имя?'
            textField.keyboard_type = ui.KEYBOARD_DEFAULT
            textField.begin_editing()
            ViewsResize()
            doneButton.enabled = True
            event.wait()
            textField.end_editing()
            ViewsResize()
            enterButton.enabled = False
            return textField.text
        elif status == 'done':
            return '' #возвращаю пустую строку, а не None, т. к. это поле необязательное
        elif status == 'stop':
            return None #типа максимизируем ошибку, по идее бд должна ругаться, если попытаться писать в нее None вместо TEXT
    
    enterButton = ui.Button(title='Enter',
        action=enter,
        background_color='ceced2',
        border_width=1,
        border_color='white',
        corner_radius=5,
        alpha=0.0,
        enabled=False)
        #hidden=False)
    doneButton = ui.Button(title='Done',
        action=done,
        background_color='ceced2',
        border_width=1,
        border_color='white',
        corner_radius=5,
        alpha=0.0,
        enabled=False)
        #hidden=False)
    localCalendarButton = ui.Button(title='📆',
        action=selectDate,
        background_color='ceced2',
        border_width=1,
        border_color='white',
        corner_radius=5,
        alpha=0.0)
        #hidden=False)
    cancelButton = ui.Button(title='❌',
        action=cancel,
        background_color='ceced2',
        border_width=1,
        border_color='white',
        corner_radius=5,
        alpha=0.0)
        #hidden=False)
    textField = ui.TextField(delegate=MyTextFieldDelegate(),
        placeholder='',
        action=enter,
        border_color='black',
        border_width=2,
        corner_radius=5,
        alpha=0.0)
        #hidden=False)
    dp = ui.DatePicker(name='Дата?',
        mode=ui.DATE_PICKER_MODE_DATE,
        background_color='white',
        border_color='black',
        border_width=2,
        corner_radius=5,
        alpha=0.0)
        #hidden=False)
    dpDoneButton = ui.Button(title='Done',
        action=dpDone,
        background_color='ceced2',
        border_width=1,
        border_color='white',
        corner_radius=5,
        alpha=0.0)
        #hidden=False)

    view.add_subview(cancelButton)
    view.add_subview(localCalendarButton)
    view.add_subview(enterButton)
    view.add_subview(doneButton)
    view.add_subview(textField)
    view.add_subview(dp)
    view.add_subview(dpDoneButton)

    a['category'] = getCategory()
    a['price'] = getPrice()
    a['name'] = getName()

    if status != 'stop' and a['price'] != None and a['category'] != None:
        a['date'] = date #по умолчанию дата = сегодня. Но если была использована кнопка smallCalendarButton, то в date лежит уже выбранная новая дата
        a['id'] = (a['date'] + ' ' + myRandom())
        a['note'] = ''

        b = list(a.values())
        
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        db.execute('INSERT INTO purchases VALUES(?, ?, ?, ?, ?, ?)', b)
        connection.commit()
        connection.close()

    date = now() #возвращаем дату обратно на сегодня
    status = 'stop'
    doneButton.enabled = False

    view.remove_subview(cancelButton)
    view.remove_subview(localCalendarButton)
    view.remove_subview(enterButton)
    view.remove_subview(doneButton)
    view.remove_subview(textField)
    view.remove_subview(dp)
    view.remove_subview(dpDoneButton)

    periodButton.enabled = True
    calendarButton.enabled = True
    settingsButton.enabled = True
    searchButton.enabled = True
    addButton.enabled = True
    table.touch_enabled = True
    table.alpha = 1.0
    tableUpdate()

    
def goToSettings(sender):
    periodButton.enabled = False
    calendarButton.enabled = False
    settingsButton.enabled = False
    searchButton.enabled = False
    addButton.enabled = False
    table.touch_enabled = False
    table.alpha = 0.5

    connection = sqlite3.connect(DB)
    #connection.row_factory = lambda cursor, row: row[0] #эта магия позволяет возвращать из db список, а не список кортежей, то есть возвращает нулевой элемент каждого кортежа
    db = connection.cursor()
    #print(db.execute('SELECT category, sum(price) FROM purchases WHERE date BETWEEN "2021-02-01" AND "2021-02-02" GROUP BY category ORDER BY sum(price) DESC').fetchall()) #выбор между днями
    print(db.execute('SELECT category, sum(price) FROM purchases WHERE strftime("%Y-%m", date) = "2021-02" GROUP BY category ORDER BY sum(price) DESC').fetchall()) #выбор за февраль 2021
    connection.close()

    periodButton.enabled = True
    calendarButton.enabled = True
    settingsButton.enabled = True
    searchButton.enabled = True
    addButton.enabled = True
    table.touch_enabled = True
    table.alpha = 1.0

def findTransaction(sender):
    periodButton.enabled = False
    calendarButton.enabled = False
    settingsButton.enabled = False
    searchButton.enabled = False
    addButton.enabled = False
    table.touch_enabled = False
    table.alpha = 0.5

    connection = sqlite3.connect(DB)
    db = connection.cursor()
    for row in db.execute('SELECT * FROM purchases'):
        print(row)
    connection.close()

    periodButton.enabled = True
    calendarButton.enabled = True
    settingsButton.enabled = True
    searchButton.enabled = True
    addButton.enabled = True
    table.touch_enabled = True
    table.alpha = 1.0







#main
#print(sys.argv[1])

if not os.path.isfile(DB):
    createDb()

#globals
mode = INITIALMODE
date = now()
endOfPeriodDate = None
keyboardFrame = None
backgroundColor = getTheme()

periodButton = ui.Button(image=ui.Image.named(PERIOD),
    action=changePeriod,
    alpha=0.0)
calendarButton = ui.Button(image=ui.Image.named(CALENDAR),
    action=selectDate,
    alpha=0.0)
settingsButton = ui.Button(image=ui.Image.named(SETTINGS),
    action=goToSettings,
    alpha=0.0)
searchButton = ui.Button(image=ui.Image.named(SEARCH),
    action=findTransaction,
    alpha=0.0)
addButton = ui.Button(image=ui.Image.named(ADD),
    action=addTransaction,
    alpha=0.0)
dataSource = MyListDataSource(items='',
    action=rowSelected,
    editAction=rowDeleted,
    accessoryAction=accessoryTaped)
table = ui.TableView(data_source=dataSource,
    delegate=dataSource,
    editing = False,
    alpha=0.0)
view = MyView(name='',
    flex='WH',
    background_color='white')

view.add_subview(periodButton)
view.add_subview(calendarButton)
view.add_subview(settingsButton)
view.add_subview(searchButton)
view.add_subview(addButton)
view.add_subview(table)

view.present(hide_close_button=False) #выставление размеров элементов происходит в MyView.layout(), автоматически каждый раз при изменении размеров view

tableUpdate()

def present():
    periodButton.alpha = 1.0
    calendarButton.alpha = 1.0
    settingsButton.alpha = 1.0
    searchButton.alpha = 1.0
    addButton.alpha = 1.0
    table.alpha = 1.0
ui.animate(present)