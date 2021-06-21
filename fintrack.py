import sys, ui, dialogs, pickle, os, sqlite3, threading, random, datetime, ctypes, console, clipboard

DB = './fintrack text primary key.db'

TABLECELLLENGHT = 30 #количесвто символов, которое помещается в одной строке таблицы (когда категория открыта), зависит от размера шрифта SMALLFONT
SMALLFONT = ('<system>', 14) #размер шрифта в таблице в открытой категории (он меньше чем шрифт самой категории)
CURRENCYSYMBOL =  ' ₽'
INITIALMODE = 'M' #режим, в котором стартует приложение по умолчанию, D = Date, M = Month, Y = Year, A = All time

DATEFORMATDAY = '%d.%m.%Y' #can be changed for your local format, default is Europe (Russia)
DATEFORMATMONTH = '%B %Y'
DATEFORMATYEAR = '%Y'

CALENDAR = 'calendar36.png'
PERIOD = 'period36.png'
ADD = 'plus36.png'
SEARCH = 'search36.png'
SETTINGS = 'settings36.png'

PERIODTABLEWIDTH = 150
PERIODTABLEHEIGHT = 300

DATEPICKERHEIGHT = 180
DATEPICKERDONEBUTTONHEIGHT = 72
DPDONEBUTTONINTRANSACTIONHEIGHT = 36
TEXTFIELDHEIGHT = 36

class GUI():
    def __init__(self,
                logic,
                name='',
                periodButtonAction=None,
                calendarButtonAction=None,
                settingsButtonAction=None,
                searchButtonAction=None,
                addButtonAction=None,
                rowSelectedAction=None,
                rowDeletedAction=None,
                rowAccessoryTapedAction=None):
        self.periodButtonAction = periodButtonAction
        self.calendarButtonAction = calendarButtonAction
        self.settingsButtonAction = settingsButtonAction
        self.searchButtonAction = searchButtonAction
        self.addButtonAction = addButtonAction
        self.rowSelectedAction = rowSelectedAction
        self.rowDeletedAction = rowDeletedAction
        self.rowAccessoryTapedAction = rowAccessoryTapedAction

        self.logic = logic #ссылка на logic-объект для определения работы режимов логики, дат и некоторых функций (Logic.cur)

        self.mode = 'start' #тут хранится состояние гуя. Оно используется в обработчиках кнопок, textField, datePicker и т. д.
        self.result = None #тут хранится результат того или иного взаимодейсвтия с gui, который будет потом передан в соответствующий метод logic
        self.event = threading.Event() #флаг для ожидания пользовательского ввода в отдельном потоке
        
        self.periodButton = ui.Button(image=ui.Image.named(PERIOD),
            action=self._periodButtonAction,
            alpha=0.0)
        self.calendarButton = ui.Button(image=ui.Image.named(CALENDAR),
            action=self._calendarButtonAction,
            alpha=0.0)
        self.settingsButton = ui.Button(image=ui.Image.named(SETTINGS),
            action=self._settingsButtonAction,
            alpha=0.0)
        self.searchButton = ui.Button(image=ui.Image.named(SEARCH),
            action=self._searchButtonAction,
            alpha=0.0)
        self.addButton = ui.Button(image=ui.Image.named(ADD),
            action=self._addButtonAction,
            alpha=0.0)
        self.mainTableDataSource = self.MyListDataSource(items='',
            action=self._mainTableRowSelectedAction,
            editAction=self._mainTableRowDeletedAction,
            accessoryAction=self._mainTableRowAccessoryTapedAction)
        self.mainTable = ui.TableView(data_source=self.mainTableDataSource,
            delegate=self.mainTableDataSource,
            editing = False,
            alpha=0.0)
        self.periodTableDataSource = ui.ListDataSource(items=('Day',
                'Month',
                'Year',
                'Period',
                'All time'))
        self.periodTableDataSource.action=self._periodTableRowSelectedAction
        self.periodTable = ui.TableView(data_source=self.periodTableDataSource,
            delegate=self.periodTableDataSource,
            editing=False,
            border_width=2,
            corner_radius=5,
            width=PERIODTABLEWIDTH,
            height=PERIODTABLEHEIGHT,
            alpha=0.0)
        self.datePicker = ui.DatePicker(name='Дата?',
            mode=ui.DATE_PICKER_MODE_DATE,
            action=self._datePickerAction,
            background_color='white',
            border_color='black',
            border_width=2,
            corner_radius=5,
            height=DATEPICKERHEIGHT,
            alpha=0.0)
        self.datePickerDoneButton = ui.Button(title='Done',
            font=('<system-bold>', 20),
            action=self._datePickerDoneButtonAction,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            height=DATEPICKERDONEBUTTONHEIGHT,
            alpha = 0.0)
        self.textField = ui.TextField(delegate=self.MyTextFieldDelegate(textFieldDidChangedAction=self._textFieldDidChanged, textFieldShouldReturnAction=self._textFieldEnterButtonAction),
            placeholder='',
            height=TEXTFIELDHEIGHT,
            border_color='black',
            border_width=2,
            corner_radius=5,
            alpha=0.0)
        self.textFieldEnterButton = ui.Button(title='Enter',
            action=self._textFieldEnterButtonAction,
            height=TEXTFIELDHEIGHT,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            alpha=0.0,
            enabled=False)
        self.textFieldDoneButton = ui.Button(title='Done',
            action=self._textFieldDoneButtonAction,
            height=TEXTFIELDHEIGHT,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            alpha=0.0,
            enabled=False)
        self.textFieldCalendarButton = ui.Button(title='📆',
            action=self._textFieldelCalendarButtonAction,
            height=TEXTFIELDHEIGHT,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            alpha=0.0)
        self.textFieldCancelButton = ui.Button(title='❌',
            action=self._textFieldCancelButtonAction,
            height=TEXTFIELDHEIGHT,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            alpha=0.0)
        self.textFieldDatePicker = ui.DatePicker(name='Дата?',
            mode=ui.DATE_PICKER_MODE_DATE,
            action=self._textFieldDatePickerAction,
            background_color='white',
            border_color='black',
            border_width=2,
            corner_radius=5,
            height=DATEPICKERHEIGHT,
            alpha=0.0)
        self.textFieldDatePickerDoneButton = ui.Button(title='Done',
            font=('<system-bold>', 20),
            action=self._textFieldDatePickerDoneButtonAction,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            height=DATEPICKERDONEBUTTONHEIGHT,
            alpha = 0.0)

        self.view = self.MyView(keyboardFrameChangedAction=self.subViewsResize,
            layoutChangedAction=self.subViewsResize,
            name=name,            
            flex='WH',
            background_color='white')

        self.view.add_subview(self.periodButton)
        self.view.add_subview(self.calendarButton)
        self.view.add_subview(self.settingsButton)
        self.view.add_subview(self.searchButton)
        self.view.add_subview(self.addButton)
        self.view.add_subview(self.mainTable)
        self.view.add_subview(self.periodTable)
        self.view.add_subview(self.datePicker)
        self.view.add_subview(self.datePickerDoneButton)
        self.view.add_subview(self.textField)
        self.view.add_subview(self.textFieldEnterButton)
        self.view.add_subview(self.textFieldDoneButton)
        self.view.add_subview(self.textFieldCalendarButton)
        self.view.add_subview(self.textFieldCancelButton)
        self.view.add_subview(self.textFieldDatePicker)
        self.view.add_subview(self.textFieldDatePickerDoneButton)
        self.view.present(hide_close_button=False)
        
        def present():
            self.periodButton.alpha = 1.0
            self.calendarButton.alpha = 1.0
            self.settingsButton.alpha = 1.0
            self.searchButton.alpha = 1.0
            self.addButton.alpha = 1.0
            self.mainTable.alpha = 1.0
        ui.animate(present)

    def _periodButtonAction(self, sender):
        #дальнейшие действия происходят в _periodTableRowSelectedAction
        def present():
            self.periodButton.enabled = False
            self.calendarButton.enabled = False
            self.settingsButton.enabled = False
            self.searchButton.enabled = False
            self.addButton.enabled = False
            self.mainTable.touch_enabled = False
            self.mainTable.alpha = 0.5
            self.periodTable.alpha = 1.0

        ui.animate(present)

    @ui.in_background
    def _calendarButtonAction(self, sender):
        def present():
            self.periodButton.enabled = False
            self.calendarButton.enabled = False
            self.settingsButton.enabled = False
            self.searchButton.enabled = False
            self.addButton.enabled = False
            self.mainTable.touch_enabled = False
            self.mainTable.alpha = 0.5
            self.datePickerDoneButton.title = 'Done'
            self.datePickerDoneButton.center = (self.datePickerDoneButton.superview.width/2,
                    (self.datePickerDoneButton.superview.height-self.addButton.height-self.datePickerDoneButton.height/2))
            self.datePicker.center = (self.datePicker.superview.width/2,
                self.datePickerDoneButton.frame[1]-self.datePicker.height/2)
            self.datePicker.alpha = 1.0
            self.datePickerDoneButton.alpha = 1.0
        
        def hide():
            self.periodButton.enabled = True
            self.calendarButton.enabled = True
            self.settingsButton.enabled = True
            self.searchButton.enabled = True
            self.addButton.enabled = True
            self.mainTable.touch_enabled = True
            self.mainTable.alpha = 1.0
            self.datePicker.alpha = 0.0
            self.datePickerDoneButton.alpha = 0.0

        def exit():
            if self.calendarButtonAction:
                self.calendarButtonAction(self.result)

        self.event.clear()
        ui.animate(present)
        self.event.wait()
        self.result = self.datePicker.date
        ui.animate(hide, completion=exit)        

    @ui.in_background
    def _settingsButtonAction(self, sender):
        def exit():
            if self.settingsButtonAction:
                self.settingsButtonAction(self.result)

        def present():
            pass

        ui.animate(present)

    @ui.in_background
    def _searchButtonAction(self, sender):
        if self.searchButtonAction:
            self.searchButtonAction(self.result)

    @ui.in_background
    def _addButtonAction(self, sender, transactionData=None):
        def present():
            self.mainTable.alpha = 0.5
            self.mainTable.touch_enabled = False

            self.periodButton.enabled = False
            self.calendarButton.enabled = False
            self.settingsButton.enabled = False
            self.searchButton.enabled = False
            self.addButton.enabled = False

            self.textFieldCancelButton.enabled = True
            self.textFieldCalendarButton.enabled = True
            self.textFieldEnterButton.enabled = False
            self.textFieldDoneButton.enabled = False

        def hide():
            self.textFieldCancelButton.alpha = 0
            self.textFieldCalendarButton.alpha = 0
            self.textFieldEnterButton.alpha = 0
            self.textFieldDoneButton.alpha = 0
            self.textField.alpha = 0

            self.textFieldCancelButton.enabled = False
            self.textFieldCalendarButton.enabled = False
            self.textFieldEnterButton.enabled = False
            self.textFieldDoneButton.enabled = False

            self.periodButton.enabled = True
            self.calendarButton.enabled = True
            self.settingsButton.enabled = True
            self.searchButton.enabled = True
            self.addButton.enabled = True

            self.mainTable.alpha = 1.0
            self.mainTable.touch_enabled = True

        def exit():
            self.status = 'start'

            if self.addButtonAction:
                self.addButtonAction(self.result)
                self.update(self.logic.getNameForGui(), self.logic.getTableItemsForGui())

        ui.animate(present)

        self.status = 'addingTransaction'

        if transactionData:
            self.result = transactionData
        else:
            self.result = {'id':None, 'name':None, 'category':None,'price':None, 'date':None, 'note':None}
        
        #запрос категории
        if self.status == 'addingTransaction':
            connection = sqlite3.connect(DB)
            connection.row_factory = lambda cursor, row: row[0] #эта магия позволяет возвращать из db список, а не список кортежей, то есть возвращает нулевой элемент каждого кортежа
            db = connection.cursor()
            categories = db.execute('SELECT name FROM categories ORDER BY id').fetchall()
            connection.close()

            selectedCategory = dialogs.list_dialog(title='Категория?', items=categories, multiple=False)

            if selectedCategory == None:
                self.status = 'start'
            else:
                self.result['category'] = selectedCategory
        
        #запрос цены
        if self.status == 'addingTransaction':
            self.event.clear() #ставим флаг ожидания ответа от пользователя, снимается он в enter() по нажатию кнопки Enter
            self.textFieldCancelButton.alpha = 1.0
            self.textFieldCalendarButton.alpha = 1.0
            self.textFieldEnterButton.alpha = 1.0
            self.textFieldDoneButton.alpha = 1.0
            self.textField.alpha = 1.0
            if self.result['price']:
                self.textField.text = self.result['price']
            else:
                self.textField.text=''
            self.textField.placeholder = 'Цена?'
            self.textField.keyboard_type = ui.KEYBOARD_DECIMAL_PAD
            self.textField.begin_editing()
            self.event.wait() #ожидаем пользовательского ввода, ждем до снятия флага, снимается он в self.textFieldEnterButton() по нажатию кнопки Enter
            self.textField.end_editing()
            self.textFieldEnterButton.enabled = False
            if self.textField.text != '':
                price = self.textField.text.replace(',','.') #чтобы десятичные дроби нормально понимал
                self.result['price'] = float(price)
            else:
                self.status = 'start'

        #запрос имени
        if self.status == 'addingTransaction':
            self.event.clear()
            if self.result['name']:
                self.textField.text = self.result['name']
            else:
                self.textField.text=''
            self.textField.placeholder = 'Имя?'
            self.textField.keyboard_type = ui.KEYBOARD_DEFAULT
            self.textField.begin_editing()
            self.textFieldDoneButton.enabled = True
            self.event.wait()
            self.textField.end_editing()
            self.textFieldEnterButton.enabled = False
            self.result['name'] = self.textField.text
        elif self.status == 'doneTransaction':
            self.result['name'] = '' #записываем пустую строку, а не None, т. к. это поле необязательное

        ui.animate(hide, completion=exit)

    def _mainTableRowSelectedAction(self, sender):
        if self.rowSelectedAction:
            self.result = sender
            self.rowSelectedAction(self.result)

    def _mainTableRowDeletedAction(self, sender):
        if self.rowDeletedAction:
            self.rowDeletedAction()

    def _mainTableRowAccessoryTapedAction(self, sender):
        if self.rowAccessoryTapedAction:
            self.result = sender
            self.rowAccessoryTapedAction(self.result)

    @ui.in_background
    def _periodTableRowSelectedAction(self, sender):
        def hide():
            self.datePicker.alpha = 0.0
            self.datePickerDoneButton.alpha = 0.0
            self.periodTable.alpha = 0.0
            self.periodButton.enabled = True
            self.calendarButton.enabled = True
            self.settingsButton.enabled = True
            self.searchButton.enabled = True
            self.addButton.enabled = True
            self.mainTable.touch_enabled = True
            self.mainTable.alpha = 1.0

        def exit():
            if self.periodButtonAction:
                self.periodButtonAction(self.result)

        if sender.items[sender.selected_row] == 'Period':
            #далее действия происходят в _datePickerAction и _datePickerDoneButtonAction
            def presentFromDate():
                self.datePickerDoneButton.center = (self.datePickerDoneButton.superview.width/2,
                    (self.datePickerDoneButton.superview.height-self.addButton.height-self.datePickerDoneButton.height/2))
                self.datePicker.center = (self.datePicker.superview.width/2,
                    self.datePickerDoneButton.frame[1]-self.datePicker.height/2)
                
                self.datePickerDoneButton.title = ('From '+self.datePicker.date.strftime(DATEFORMATDAY))
                self.datePickerDoneButton.enabled = True
                self.periodTable.alpha = 0.0
                self.datePicker.alpha = 1.0
                self.datePickerDoneButton.alpha = 1.0
            
            def hidePeriod():
                self.datePicker.alpha = 0.0
                self.datePickerDoneButton.alpha = 0.0

            def presentToDate():
                self.datePickerDoneButton.center = (self.datePickerDoneButton.superview.width/2,
                    (self.datePickerDoneButton.superview.height-self.addButton.height-self.datePickerDoneButton.height/2))
                self.datePicker.center = (self.datePicker.superview.width/2,
                    self.datePickerDoneButton.frame[1]-self.datePicker.height/2)
                self.datePickerDoneButton.title = ('To '+self.datePicker.date.strftime(DATEFORMATDAY))
                self.datePicker.alpha = 1.0
                self.datePickerDoneButton.alpha = 1.0

            self.mode = 'selectingFromDate'
            self.event.clear()            
            ui.animate(presentFromDate)
            self.event.wait() #ожидаем пользовательского ввода, ждем до снятия флага, снимается он в _datePickerDoneButtonAction
            fromDate = self.datePicker.date
            ui.animate(hidePeriod)
            self.mode = 'selectingToDate'
            self.event.clear()
            ui.animate(presentToDate)
            self.event.wait()
            toDate = self.datePicker.date
            self.mode = 'start'
            self.result = (sender.items[sender.selected_row], fromDate, toDate)
        else:        
            self.result = (sender.items[sender.selected_row], )
        
        ui.animate(hide, completion=exit)

    def _datePickerAction(self, sender): #тут будем менять заголовок кнопки datePickerDoneButton в режиме выбора периода дат, с 'From datePicker.date' на 'To datePickerDate'
        if self.mode == 'selectingFromDate':
            self.datePickerDoneButton.title = 'From   ' + self.datePicker.date.strftime(DATEFORMATDAY)
        elif self.mode == 'selectingToDate':
            self.datePickerDoneButton.title = 'To   ' + self.datePicker.date.strftime(DATEFORMATDAY)
        else:
            pass

    def _datePickerDoneButtonAction(self, sender):
        self.event.set()

    def _textFieldDidChanged(self, textfield):
        if self.textField.text != '':
            self.textFieldEnterButton.enabled = True
            self.textFieldDoneButton.enabled = True
        else:
            self.textFieldEnterButton.enabled = False
            self.textFieldDoneButton.enabled = False
    
    def _textFieldEnterButtonAction(self, sender):
        self.event.set()

    def _textFieldDoneButtonAction(self, sender):
        self.status = 'doneTransaction'
        self.event.set()

    def _textFieldelCalendarButtonAction(self, sender):
        self.textFieldDatePickerDoneButton.enabled = True
        self.textFieldDatePickerDoneButton.alpha = 1.0
        self.textFieldDatePicker.alpha = 1.0

        self.textFieldCancelButton.enabled = False
        self.textFieldCalendarButton.enabled = False
        self.textFieldEnterButton.enabled = False
        self.textFieldDoneButton.enabled = False

    def _textFieldCancelButtonAction(self, sender):
        self.status = 'start'
        self.event.set()

    def _textFieldDatePickerAction(self, sender):
        pass

    def _textFieldDatePickerDoneButtonAction(self, sender):
        self.result['date'] = str(self.textFieldDatePicker.date)
        def hide():
            self.textFieldDatePicker.alpha = 0
            self.textFieldDatePickerDoneButton.alpha = 0
            #self.textField.enabled = True
            self.textFieldCancelButton.enabled = True
            self.textFieldCalendarButton.enabled = True
            if self.textField.text != '':
                self.textFieldEnterButton.enabled = True
            if self.result['category'] != None and self.textField.text != '':
                self.textFieldDoneButton.enabled = True
        ui.animate(hide)

    def subViewsResize(self):
        #сюда попадаем либо при ручном вызове, либо атвоматически при изменении self.view.layout (например поворот экрана), либо при появлении/скрытии клавиатуры. Это описано в class MyView(ui.View)
        #высоты элементов задаются при создании элементов
        #ширины основных кнопок зависят от картинок
        
        self.periodButton.center = (self.periodButton.superview.width*0.1,
            (self.periodButton.superview.height-(self.periodButton.height/2)))
        self.calendarButton.center = (self.calendarButton.superview.width*0.3,
            (self.calendarButton.superview.height-(self.calendarButton.height/2)))
        self.settingsButton.center = (self.settingsButton.superview.width*0.5,
            (self.settingsButton.superview.height-(self.settingsButton.height/2)))
        self.searchButton.center = (self.searchButton.superview.width*0.7,
            (self.searchButton.superview.height-(self.searchButton.height/2)))
        self.addButton.center = (self.addButton.superview.width*0.9,
            (self.addButton.superview.height-(self.addButton.height/2)))
        self.mainTable.width = self.mainTable.superview.width
        self.mainTable.height = (self.mainTable.superview.height-self.periodButton.height)
        self.mainTable.center = (self.mainTable.superview.width/2,
            (self.mainTable.superview.height-self.periodButton.height-(self.mainTable.height/2)))
        self.periodTable.size_to_fit() #выставляет только высоту почему-то
        self.periodTable.center = (self.periodTable.width/2,
            (self.periodTable.superview.height - self.periodButton.height - self.periodTable.height/2))
        
        self.datePickerDoneButton.width = self.datePickerDoneButton.superview.width
        self.datePickerDoneButton.center = (self.datePickerDoneButton.superview.width/2,
            self.periodButton.frame[1] - self.datePickerDoneButton.height/2)
        self.datePicker.width = self.datePicker.superview.width
        self.datePicker.center = (self.datePicker.superview.width/2,
            self.datePickerDoneButton.frame[1]-self.datePicker.height/2)

        if self.view.keyboardFrame == (0.00, 0.00, 0.00, 0.00): #клавиатура на экране отсутствует
            self.textField.alpha = 0.0
            self.textFieldCancelButton.alpha = 0.0
            self.textFieldCalendarButton.alpha = 0.0
            self.textFieldEnterButton.alpha = 0.0
            self.textFieldDoneButton.alpha = 0.0
        else: #клавиатура на экране присутствует
            base = self.view.keyboardFrame[1]
            
            self.textFieldCancelButton.width = self.textFieldCancelButton.superview.width/8
            self.textFieldCancelButton.center = (self.textFieldCancelButton.superview.width/16,
                base - self.textFieldCancelButton.height/2)
            self.textFieldCalendarButton.width = self.textFieldCalendarButton.superview.width/8
            self.textFieldCalendarButton.center = (self.textFieldCalendarButton.superview.width*0.1875,
                base - self.textFieldCalendarButton.height/2)
            self.textFieldEnterButton.width = self.textFieldEnterButton.superview.width/2
            self.textFieldEnterButton.center = (self.textFieldEnterButton.superview.width/2,
                base - self.textFieldEnterButton.height/2)
            self.textFieldDoneButton.width = self.textFieldDoneButton.superview.width/4
            self.textFieldDoneButton.center = (self.textFieldDoneButton.superview.width*0.875,
                base - self.textFieldDoneButton.height/2)
            self.textField.width = self.textField.superview.width
            self.textField.center = (self.textField.superview.width/2,
                base - self.textFieldCancelButton.height-self.textField.height/2)

            self.textField.alpha = 1.0
            self.textFieldCancelButton.alpha = 1.0
            self.textFieldCalendarButton.alpha = 1.0
            self.textFieldEnterButton.alpha = 1.0
            self.textFieldDoneButton.alpha = 1.0

        self.textFieldDatePickerDoneButton.width = self.textFieldDatePickerDoneButton.superview.width
        self.textFieldDatePickerDoneButton.center = (self.textFieldDatePickerDoneButton.superview.width/2,
            self.textField.frame[1] - self.textFieldDatePickerDoneButton.height/2)
        self.textFieldDatePicker.width = self.textFieldDatePicker.superview.width
        self.textFieldDatePicker.center = (self.textFieldDatePicker.superview.width/2,
            self.textFieldDatePickerDoneButton.frame[1]-self.datePicker.height/2)        
    
    def insertRows(self, rowsToInsert):
        self.mainTable.insert_rows(rowsToInsert)

    def deleteRows(self, rowsToDelete):
        self.mainTable.delete_rows(rowsToDelete)

    def update(self, name, tableItems):
        self.view.name = name
        self.mainTableDataSource.items = tableItems
        self.mainTable.reload()
    
    def addTransaction(self, transactionData=None):
        self._addButtonAction(None, transactionData)

    class MyListDataSource():
        #пилим свои методы, т. к. в ui.ListDataSource нет поддержки секций для табицы.

        #items = [{'sectionName':'', 'sectionSum':'', 'rows':[{'rowId':'', 'rowName':'', 'rowSum':''}, {'rowId':'', 'rowName':'', 'rowSum':''}, {'rowId':'', 'rowName':'', 'rowSum':''}]},
        #         {'sectionName':'', 'sectionSum':'', 'rows':[{'rowId':'', 'rowName':'', 'rowSum':''}, {'rowId':'', 'rowName':'', 'rowSum':''}, {'rowId':'', 'rowName':'', 'rowSum':''}]},
        #         {'sectionName':'', 'sectionSum':'', 'rows':[{'rowId':'', 'rowName':'', 'rowSum':''}, {'rowId':'', 'rowName':'', 'rowSum':''}, {'rowId':'', 'rowName':'', 'rowSum':''}]}]
        
        #sectionName = название секции, то есть категория транзакций
        #sectionSum = сумма всех цен транзакций в данной категории
        #rowId = id транзакции, не отображается в таблице, но нужен для редактирования транзакции при нажатии на строку таблицы. По этому id идет обращение к БД
        #rowName = имя транзакции
        #rowSum = цена транзакции

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
            if self.items !=None:
                return len(self.items)
            else:
                return 0

        def tableview_number_of_rows(self, tv, section):
            if self.items != None:
                return len(self.items[section]['rows'])
            else:
                return 0

        def tableview_can_delete(self, tv, section, row):
            return self.delete_enabled

        def tableview_can_move(self, tv, section, row):
            return self.move_enabled

        def tableview_title_for_header(self, tv, section):
            if self.items[section]['sectionName'] == '':
                return ''
            else:
                return (self.items[section]['sectionName']+'\t('+self.items[section]['sectionSum']+')')

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
        def __init__(self, keyboardFrameChangedAction, layoutChangedAction, name, flex, background_color):
            self.keyboardFrame = (0.00, 0.00, 0.00, 0.00)
            self.keyboardFrameChangedAction = keyboardFrameChangedAction
            self.layoutChangedAction = layoutChangedAction
            self.name = name
            self.flex = flex
            self.background_color = background_color

        def keyboard_frame_will_change(self, frame):
            self.keyboardFrame = ui.convert_rect(frame, to_view=self)
            self.keyboardFrameChangedAction()

        def will_close(self):
            pass
        
        def layout(self):
            self.layoutChangedAction()

    class MyTextFieldDelegate():
        def __init__(self, textFieldDidChangedAction, textFieldShouldReturnAction):
            self.textFieldDidChangedAction = textFieldDidChangedAction
            self.textFieldShouldReturnAction = textFieldShouldReturnAction

        def textfield_did_change(self, textfield):
            self.textFieldDidChangedAction(textfield)

        def textfield_should_return(self, textfield): #here we are when you pressing Return button on screen keyboard
            self.textFieldShouldReturnAction(textfield)

class Logic():
    def __init__(self):
        self.mode = INITIALMODE
        self.date = self.now() #datetime object
        self.fromDate = None #datetime object
        self.toDate = None #datetime object
        if not os.path.isfile(DB):
            self.createDb()

    def periodButtonAction(self, result):
        if result[0] == 'Day':
            self.mode = 'D'
        elif result[0] == 'Month':
            self.mode = 'M'
        elif result[0] == 'Year':
            self.mode = 'Y'
        elif result[0] == 'Period':
            self.mode = 'P'
            self.fromDate = result[1]
            self.toDate = result[2]
        elif result[0] == 'All time':
            self.mode = 'All'
        else:
            raise ValueError('Несоответствующее значение')
        gui.update(logic.getNameForGui(), logic.getTableItemsForGui())     

    def calendarButtonAction(self, result):
        self.date = result
        gui.update(logic.getNameForGui(), logic.getTableItemsForGui())

    def settingsButtonAction(self):
        print('settingsButtonAction')

    def searchButtonAction(self):
        print('searchButtonAction')

    def addButtonAction(self, result):
        if result['id'] and result['category'] and result['price']: #режим редактирования транзакции, будем ее перезаписывать по этому id
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            db.execute('UPDATE purchases SET name=?, category=?, price=?, date=?, note=? WHERE id=?', (result['name'], result['category'], result['price'], result['date'], result['note'], result['id']))
            connection.commit()
            connection.close() 
        elif result['category'] and result['price']: #режим добавления транзакции
            if not result['date']:
                result['date'] = str(self.now())
            result['id'] = (result['date']+' '+self.myRandom())
            result['note'] = ''

            a = list(result.values())

            connection = sqlite3.connect(DB)
            db = connection.cursor()
            db.execute('INSERT INTO purchases VALUES(?, ?, ?, ?, ?, ?)', a)
            connection.commit()
            connection.close()
        else:
            raise ValueError('В транзакции отсутствует обязательное(ые) поле(я). Category и/или Price')

    def mainTableRowSelectedAction(self, sender):
        #sender = tableView from GUI
        #sender.items = [{'sectionName':'', 'sectionSum':'', 'rows':[{'rowId':'', 'rowName':'', 'rowSum':''}, {'rowId':'', 'rowName':'', 'rowSum':''}]},
        #                {'sectionName':'', 'sectionSum':'', 'rows':[{'rowId':'', 'rowName':'', 'rowSum':''}, {'rowId':'', 'rowName':'', 'rowSum':''}]},
        #                {'sectionName':'', 'sectionSum':'', 'rows':[{'rowId':'', 'rowName':'', 'rowSum':''}, {'rowId':'', 'rowName':'', 'rowSum':''}]}]
        def getRowFromDb(sender, mask, date, category):
            rows = []
            a = (mask, date, category)
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            for index, row in enumerate(db.execute('SELECT date(date), name, price, id FROM purchases WHERE strftime(?, date) = ? AND category = ? ORDER BY date DESC', a)):
                sender.items[sender.selected_section]['rows'].append({'rowId':row[3], 'rowName':str(row[0]+' '+str(row[1])), 'rowSum':self.cur(row[2])})
                rows.append((index+1, sender.selected_section)) #+1 потому что 0 строка - это Total:
            connection.close()
            return rows

        def getRowFromDbPeriod(sender, mask, fromDate, toDate, category):
            rows = []
            a = (mask, fromDate, toDate, category)
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            for index, row in enumerate(db.execute('SELECT date(date), name, price, id FROM purchases WHERE strftime(?, date) BETWEEN ? AND ? AND category = ? ORDER BY date DESC', a)):
                sender.items[sender.selected_section]['rows'].append({'rowId':row[3], 'rowName':str(row[0]+' '+str(row[1])), 'rowSum':self.cur(row[2])})
                rows.append((index+1, sender.selected_section)) #+1 потому что 0 строка - это Total:
            connection.close()
            return rows

        def getRowFromDbAll(sender, category):
            rows = []
            a = (category, )
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            for index, row in enumerate(db.execute('SELECT date(date), name, price, id FROM purchases WHERE category = ? ORDER BY date DESC', a)):
                sender.items[sender.selected_section]['rows'].append({'rowId':row[3], 'rowName':str(row[0]+' '+str(row[1])), 'rowSum':self.cur(row[2])})
                rows.append((index+1, sender.selected_section)) #+1 потому что 0 строка - это Total:
            connection.close()
            return rows

        def getRowsToDelete(sender):
            rows = []
            for i in range((sender.tableview_number_of_rows(None, sender.selected_section)-1), 0, -1):
                rows.append((i, sender.selected_section))
            return rows

        if sender.items[sender.selected_section]['sectionName'] == '': #нажата секция для развертывания списка
            category = sender.items[sender.selected_section]['rows'][sender.selected_row]['rowName']
            total = sender.items[sender.selected_section]['rows'][sender.selected_row]['rowSum']
            sender.items[sender.selected_section]['sectionName'] = category
            sender.items[sender.selected_section]['sectionSum'] = total
            sender.items[sender.selected_section]['rows'] = [{'rowId':'', 'rowName':'^', 'rowSum':''}, ]
            sender.tableview.reload()
            
            if self.mode == 'D':
                r = getRowFromDb(sender, '%Y-%m-%d', self.date.strftime('%Y-%m-%d'), category)
                gui.insertRows(r)                
            elif self.mode == 'M':
                r = getRowFromDb(sender, '%Y-%m', self.date.strftime('%Y-%m'), category)
                gui.insertRows(r)                
            elif self.mode == 'Y':
                b = getRowFromDb(sender, '%Y', self.date.strftime('%Y'), category)
                gui.insertRows(b)
            elif self.mode == 'P':
                r = getRowFromDbPeriod(sender, '%Y-%m-%d', self.fromDate.strftime('%Y-%m-%d'), self.toDate.strftime('%Y-%m-%d'), category)
                gui.insertRows(r)
            elif self.mode == 'All':
                r = getRowFromDbAll(sender, category)
                gui.insertRows(r)
            else:
                raise ValueError('Несоответствующее значение')    
        elif sender.items[sender.selected_section]['rows'][sender.selected_row]['rowName'] == '^': #нажата строка Total для сворачивания списка
            r = getRowsToDelete(sender) #это нужно сделать до модификации sender.items для корректного подсчета количества строк для удаления
            c = [{'rowId':'', 'rowName':sender.items[sender.selected_section]['sectionName'], 'rowSum':sender.items[sender.selected_section]['sectionSum']}, ]
            sender.items[sender.selected_section]['sectionName'] = ''
            sender.items[sender.selected_section]['sectionSum'] = ''
            sender.tableview.reload()
            sender.items[sender.selected_section]['rows'] = c
            gui.deleteRows(r)
        else: #нажата конкретная транзакция для ее редактирования
            pass
            
    def mainTableRowDeletedAction(self):
        pass

    def mainTableRowAccessoryTapedAction(self, sender):
        @ui.in_background
        def showTransaction(title, result):
            a = console.alert(title=title, message=result, button1='Copy', button2='Ok', hide_cancel_button=True)
            if a == 1:
                clipboard.set(result)

        if sender.items[sender.tapped_accessory_section]['rows'][sender.tapped_accessory_row]['rowName'] == '^':
            print('in progress')
        else:
            transactionId = sender.items[sender.tapped_accessory_section]['rows'][sender.tapped_accessory_row]['rowId']
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            res = db.execute('SELECT id, date(date), category, name, price, note FROM purchases WHERE id = ?', (transactionId, )).fetchone()
            connection.close()
            title = 'Transaction data'
            fullRes = 'ID: '+res[0]+'\nDate: '+res[1]+'\nCategory: '+res[2]+'\nName: '+res[3]+'\nPrice: '+str(res[4])+'\nNote: '+res[5]

            showTransaction(title, fullRes)

    def datePickerDoneButtonAction(self):
        pass

    def textFieldEnterButtonAction(self):
        pass

    def textFieldDoneButtonAction(self):
        pass

    def textFieldelCalendarButtonAction(self):
        pass

    def textFieldCancelButtonAction(self):
        pass

    def cur(self, price, mode='rough'):
        if price == None:
            return '0₽'
        elif mode == 'rough':
            return (format(price, ',.0f').replace(',', '  ')+CURRENCYSYMBOL)
        elif mode == 'precisely':
            return (format(price, ',.2f').replace(',', '  ')+CURRENCYSYMBOL)
        else:
            raise ValueError('mode: несоответствующее значение')

    def myRandom(self):
        return str(random.randint(0, 9999))

    def createDb(self):
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

    def getTheme(self):
        return ui.get_ui_style()

    def now(self):
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        now = db.execute('SELECT datetime("now", "localtime")').fetchone()[0]
        connection.close()
        return datetime.datetime.strptime(now, '%Y-%m-%d %H:%M:%S')

    def getNameForGui(self):
        if self.mode == 'D':
            maskAndDate = ('%Y-%m-%d', self.date.strftime('%Y-%m-%d'))
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            total = db.execute('SELECT sum(price) FROM purchases WHERE strftime(?, date) = ?', maskAndDate).fetchone()[0]
            connection.close()
            return (self.date.strftime(DATEFORMATDAY)+' ('+self.cur(total)+')')
        elif self.mode == 'M':
            maskAndDate = ('%Y-%m', self.date.strftime('%Y-%m'))
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            total = db.execute('SELECT sum(price) FROM purchases WHERE strftime(?, date) = ?', maskAndDate).fetchone()[0]
            connection.close()
            return (self.date.strftime(DATEFORMATMONTH)+' ('+self.cur(total)+')')
        elif self.mode == 'Y':
            maskAndDate = ('%Y', self.date.strftime('%Y'))
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            total = db.execute('SELECT sum(price) FROM purchases WHERE strftime(?, date) = ?', maskAndDate).fetchone()[0]
            connection.close()
            return (self.date.strftime(DATEFORMATYEAR)+' ('+self.cur(total)+')')
        elif self.mode == 'P':
            maskAndDate = ('%Y-%m-%d', self.fromDate.strftime('%Y-%m-%d'), self.toDate.strftime('%Y-%m-%d'))
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            total = db.execute('SELECT sum(price) FROM purchases WHERE strftime(?, date) BETWEEN ? AND ?', maskAndDate).fetchone()[0]
            connection.close()
            return (self.fromDate.strftime(DATEFORMATDAY)+' - '+self.toDate.strftime(DATEFORMATDAY)+' ('+self.cur(total)+')')
        elif self.mode == 'All':
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            total = db.execute('SELECT sum(price) FROM purchases').fetchone()[0]
            connection.close()
            return ('All'+' ('+self.cur(total)+')')
        else:
            raise ValueError('Несоответствующее значение')

    def getTableItemsForGui(self):
        if self.mode == 'D':
            maskAndDate = ('%Y-%m-%d', self.date.strftime('%Y-%m-%d'))
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            result =[]
            for row in db.execute('SELECT category, sum(price) FROM purchases WHERE strftime(?, date) = ? GROUP BY category ORDER BY sum(price) DESC', maskAndDate):
                result.append({'sectionName':'', 'sectionSum':'', 'rows':[{'rowName':str(row[0]), 'rowSum':self.cur(row[1])}]})
            connection.close()
            return result
        elif self.mode == 'M':
            maskAndDate = ('%Y-%m', self.date.strftime('%Y-%m'))
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            result =[]
            for row in db.execute('SELECT category, sum(price) FROM purchases WHERE strftime(?, date) = ? GROUP BY category ORDER BY sum(price) DESC', maskAndDate):
                result.append({'sectionName':'', 'sectionSum':'', 'rows':[{'rowName':str(row[0]), 'rowSum':self.cur(row[1])}]})
            connection.close()
            return result
        elif self.mode == 'Y':
            maskAndDate = ('%Y', self.date.strftime('%Y'))
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            result =[]
            for row in db.execute('SELECT category, sum(price) FROM purchases WHERE strftime(?, date) = ? GROUP BY category ORDER BY sum(price) DESC', maskAndDate):
                result.append({'sectionName':'', 'sectionSum':'', 'rows':[{'rowName':str(row[0]), 'rowSum':self.cur(row[1])}]})
            connection.close()
            return result
        elif self.mode == 'P':
            maskAndDate = ('%Y-%m-%d', self.fromDate.strftime('%Y-%m-%d'), self.toDate.strftime('%Y-%m-%d'))
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            result =[]
            for row in db.execute('SELECT category, sum(price) FROM purchases WHERE strftime(?, date) BETWEEN ? AND ? GROUP BY category ORDER BY sum(price) DESC', maskAndDate):
                result.append({'sectionName':'', 'sectionSum':'', 'rows':[{'rowName':str(row[0]), 'rowSum':self.cur(row[1])}]})
            connection.close()
            return result
        elif self.mode == 'All':
            connection = sqlite3.connect(DB)
            db = connection.cursor()
            result =[]
            for row in db.execute('SELECT category, sum(price) FROM purchases GROUP BY category ORDER BY sum(price) DESC'):
                result.append({'sectionName':'', 'sectionSum':'', 'rows':[{'rowName':str(row[0]), 'rowSum':self.cur(row[1])}]})
            connection.close()
            return result
        else:
            raise ValueError('Несоответствующее значение')

    def vibrate(self):
        c = ctypes.CDLL(None)
        p = c.AudioServicesPlaySystemSound
        p.restype, p.argtypes = None, [ctypes.c_int32]
        vibrate_id = 0x00000fff
        p(vibrate_id)

logic = Logic()
gui = GUI(logic=logic,
        name='',
        periodButtonAction=logic.periodButtonAction,
        calendarButtonAction=logic.calendarButtonAction,
        settingsButtonAction=logic.settingsButtonAction,
        searchButtonAction=logic.searchButtonAction,
        addButtonAction=logic.addButtonAction,
        rowSelectedAction=logic.mainTableRowSelectedAction,
        rowDeletedAction=logic.mainTableRowDeletedAction,
        rowAccessoryTapedAction=logic.mainTableRowAccessoryTapedAction)
gui.update(logic.getNameForGui(), logic.getTableItemsForGui())
