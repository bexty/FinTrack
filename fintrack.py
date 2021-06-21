import sys, ui, dialogs, pickle, os, sqlite3, threading, datetime, ctypes, console, clipboard

DB = '/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/FinTrack/fintrack.db' #sqlite3 db

TABLECELLLENGHT = 30 #количесвто символов, которое помещается в одной строке таблицы (когда категория открыта), зависит от размера шрифта SMALLFONT
SMALLFONT = ('<system>', 14) #размер шрифта в таблице в открытой категории (он меньше чем шрифт самой категории)
INITIALMODE = 'M' #режим, в котором стартует приложение по умолчанию, D = Date, M = Month, Y = Year, A = All time

CURRENCYSYMBOL =  ' ₽'
DEFAULTDATEFORMATDAY = '%Y-%m-%d' #defaul date format from sqlite3
LOCALDATEFORMATDAY = '%d.%m.%Y' #can be changed for your local format, this is the Europe (Russia)
LOCALDATEFORMATMONTH = '%B %Y'
LOCALDATEFORMATYEAR = '%Y'

CALENDAR = 'calendar36.png'
PERIOD = 'period36.png'
ADD = 'plus36.png'
SEARCH = 'search36.png'
SETTINGS = 'settings36.png'

PERIODTABLEWIDTH = 150
PERIODTABLEHEIGHT = 300

DATEPICKERHEIGHT = 180
DATEPICKERDONEBUTTONHEIGHT = 72
DPDONEBUTTONINTRANSACTIONHEIGHT = 54
TEXTFIELDHEIGHT = 54
BUTTONSFONT = ('<system-bold>', 20) #так регулируется высота кнопок, а не параметром heigth

class GUI():
    def __init__(self, controller):
        self.controller = controller

        self.mode = 'start' #тут хранится состояние гуя. Оно используется в обработчиках кнопок, textField, datePicker и т. д.
        self.result = None #тут хранится результат того или иного взаимодейсвтия с gui, который будет потом передан в соответствующий метод logic
        self.event = threading.Event() #флаг для ожидания пользовательского ввода в отдельном потоке
        self.categories = self.controller.getCategories() #список категорий, нужен при добавлении транзакции

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
        self.mainTableDataSource = self.DbListDataSource(items=None,
            action=self._mainTableRowSelectedAction,
            editAction=self._mainTableRowDeletedAction,
            accessoryAction=self._mainTableRowAccessoryTapedAction)
        self.mainTable = ui.TableView(data_source=self.mainTableDataSource,
            delegate=self.mainTableDataSource,
            editing = False,
            alpha=0.0)
        self.periodTableDataSource = self.TitledListDataSource(items=('Day',
                    'Month',
                    'Year',
                    'Period',
                    'All time'),
            title='Period?',
            action=self._periodTableRowSelectedAction)
        self.periodTable = ui.TableView(data_source=self.periodTableDataSource,
            delegate=self.periodTableDataSource,
            editing=False,
            border_width=2,
            corner_radius=5,
            width=PERIODTABLEWIDTH,
            height=PERIODTABLEHEIGHT,
            scroll_enabled=False,
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
            font=BUTTONSFONT,
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
            font=BUTTONSFONT,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            alpha=0.0,
            enabled=False)
        self.textFieldDoneButton = ui.Button(title='Done',
            action=self._textFieldDoneButtonAction,
            font=BUTTONSFONT,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            alpha=0.0,
            enabled=False)
        self.textFieldCalendarButton = ui.Button(title='📆',
            action=self._textFieldelCalendarButtonAction,
            font=BUTTONSFONT,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            alpha=0.0)
        self.textFieldCancelButton = ui.Button(title='❌',
            action=self._textFieldCancelButtonAction,
            font=BUTTONSFONT,
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
            font=BUTTONSFONT,
            action=self._textFieldDatePickerDoneButtonAction,
            background_color='ceced2',
            border_width=1,
            border_color='white',
            corner_radius=5,
            height=DATEPICKERDONEBUTTONHEIGHT,
            alpha = 0.0)

        self.view = self.MyView(keyboardFrameChangedAction=self.subViewsResize,
            layoutChangedAction=self.subViewsResize,
            name='',            
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
        self.view.present(hide_close_button=False, style='popover', orientations=['portrait'])
        
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
            self.controller.calendarButtonAction(self.result)

        self.event.clear()
        ui.animate(present)
        self.event.wait()
        self.result = self.datePicker.date
        ui.animate(hide, completion=exit)        

    @ui.in_background
    def _settingsButtonAction(self, sender):
        print(dialogs.list_dialog(title='Period?', items=['Day', 'Month', 'Year', 'All time', 'Custom period']))

    @ui.in_background
    def _searchButtonAction(self, sender):
        print(dialogs.date_dialog(title='Date?'))

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
            if self.status == 'addingTransaction' or self.status == 'doneTransaction':
                self.status = 'start'
                self.controller.addButtonAction(self.result)
                self.update(self.controller.getNameForMainTable(), self.controller.getItemsForMainTable())

        ui.animate(present)

        self.status = 'addingTransaction'

        if transactionData:
            self.result = transactionData
        else:
            self.result = {'id':None, 'name':None, 'category':None,'price':None, 'date':None, 'note':None}
        
        #запрос категории
        if self.status == 'addingTransaction':
            selectedCategory = dialogs.list_dialog(title='Категория?', items=self.categories, multiple=False)

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
                self.textField.text = str(self.result['price'])
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
        #sender = tableView.datasource from GUI
        if sender.items[sender.selected_section]['sectionState'] == 'collapsed': #нажата секция для развертывания списка
            sender.items[sender.selected_section]['sectionState'] = 'expanded'
            insertList = [(x+1, sender.selected_section) for x in range(sender.items[sender.selected_section]['rows'][0]['rowSum'])] #смортим в numberOfRows
            sender.tableview.insert_rows(insertList)
            sender.reload()
        elif sender.items[sender.selected_section]['rows'][sender.selected_row]['rowName'] == 'Total:': #нажата строка Total для сворачивания списка
            sender.items[sender.selected_section]['sectionState'] = 'collapsed'
            #deleteList = [(x+1, sender.selected_section) for x in range(sender.items[sender.selected_section]['rows'][0]['rowSum'])] #смортим в numberOfRows
            #sender.tableview.delete_rows(deleteList) #как-то некрасиво работает, лучше уж совсем без анимации
            sender.reload()
        else: #нажата конкретная транзакция для ее редактирования
            rowId = (sender.items[sender.selected_section]['rows'][sender.selected_row]['rowId'])
            sender.reload()
            transactionData = self.controller.getTransaction(rowId)
            self._addButtonAction(None, transactionData)

    def _mainTableRowDeletedAction(self, sender, rowId, rowSum):
        self.controller.mainTableRowDeletedAction(sender, rowId, rowSum)
        sender.reload()

    def _mainTableRowAccessoryTapedAction(self, sender):
        self.result = sender
        self.controller.mainTableRowAccessoryTapedAction(self.result)

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
            self.controller.periodButtonAction(self.result)

        if sender.items[sender.selected_row] == 'Period':
            #далее действия происходят в _datePickerAction и _datePickerDoneButtonAction
            def presentFromDate():
                self.datePickerDoneButton.center = (self.datePickerDoneButton.superview.width/2,
                    (self.datePickerDoneButton.superview.height-self.addButton.height-self.datePickerDoneButton.height/2))
                self.datePicker.center = (self.datePicker.superview.width/2,
                    self.datePickerDoneButton.frame[1]-self.datePicker.height/2)
                
                self.datePickerDoneButton.title = ('From '+self.datePicker.date.strftime(LOCALDATEFORMATDAY))
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
                self.datePickerDoneButton.title = ('To '+self.datePicker.date.strftime(LOCALDATEFORMATDAY))
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
            self.datePickerDoneButton.title = 'From   ' + self.datePicker.date.strftime(LOCALDATEFORMATDAY)
        elif self.mode == 'selectingToDate':
            self.datePickerDoneButton.title = 'To   ' + self.datePicker.date.strftime(LOCALDATEFORMATDAY)
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

    def deleteRows(self, rowsToDelete):
        self.mainTable.delete_rows(rowsToDelete)

    def update(self, name, tableItems):
        self.view.name = name
        self.mainTableDataSource.items = tableItems
        self.mainTable.reload()

    class DbListDataSource():
        #определяем свой формат данных, пилим свои методы, т. к. в ui.ListDataSource нет поддержки секций для табицы.

        #items = [{'sectionState':'collapsed', 'sectionName':'', 'sectionSum':'', 'rows':[{'rowId':'', 'rowDate':'', 'rowName':'Total:', 'rowSum':'numberOfRows'}, {'rowId':'', 'rowDate':'', 'rowName':'', 'rowSum':''}]},
        #         {'sectionState':'expanded' , 'sectionName':'', 'sectionSum':'', 'rows':[{'rowId':'', 'rowDate':'', 'rowName':'Total:', 'rowSum':'numberOfRows'}, {'rowId':'', 'rowDate':'', 'rowName':'', 'rowSum':''}]},
        #         {'sectionState':'expanded' , 'sectionName':'', 'sectionSum':'', 'rows':[{'rowId':'', 'rowDate':'', 'rowName':'Total:', 'rowSum':'numberOfRows'}, {'rowId':'', 'rowDate':'', 'rowName':'', 'rowSum':''}]}]
        
        #sectionState = свернута или развернута секция (collapsed, expanded)
        #sectionName = название секции, то есть категория транзакций
        #sectionSum = сумма всех цен транзакций в данной категории
        #rowId = id транзакции, не отображается в таблице, но нужен для редактирования транзакции при нажатии на строку таблицы. По этому id идет обращение к БД
        #rowDate = дата транзакции
        #rowName = имя транзакции
        #rowSum = цена транзакции
        #первая строка в каждой секции - Total: numberOfRows. Сделано для сворачивания секции. Отображает количество строк в данной секции

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
            self.number_of_lines = 0 #uses as many lines, as needed to display a text

        def reload(self):
            if self.tableview and not self.reload_disabled:
                self.tableview.reload()

        def tableview_cell_for_row(self, tv, section, row):
            self.tableview = tv
            cell = ui.TableViewCell(style='value1')

            if self.items[section]['sectionState'] == 'collapsed': #при свернутой секции у нас в ней всегда будет только одна строка с названием секции и суммой секции
                item1 = self.items[section]['sectionName'] #sectionName
                item2 = str(self.items[section]['sectionSum']) #sectionSum
                cell.text_label.number_of_lines = self.number_of_lines
                cell.detail_text_label.text = item2
                cell.text_label.text = item1
                cell.selectable = False
                return cell
            elif self.items[section]['sectionState'] == 'expanded':
                if self.items[section]['rows'][row]['rowDate']: #показываем транзакцию
                    if self.items[section]['rows'][row]['rowName'] == '':
                        item1 = self.items[section]['rows'][row]['rowDate']
                    else:
                        item1 = self.items[section]['rows'][row]['rowDate'] + '\n' + self.divideString(TABLECELLLENGHT, self.items[section]['rows'][row]['rowName']) #rowDate + rowName. rowName разбит на строки не длиннее TABLECELLLENGHT
                    cell.accessory_type = 'detail_button'
                else:
                    item1 = self.items[section]['rows'][row]['rowName'] #показываем строку Total:
                item2 = str(self.items[section]['rows'][row]['rowSum']) #rowSum
                cell.text_label.number_of_lines = self.number_of_lines
                cell.detail_text_label.text = item2
                cell.text_label.text = item1
                cell.text_label.font = SMALLFONT
                cell.detail_text_label.font = SMALLFONT
                cell.selectable = False
                return cell

        def tableview_number_of_sections(self, tv):
            self.tableview = tv
            if self.items:
                return len(self.items)
            else:
                return 0

        def tableview_number_of_rows(self, tv, section):
            if self.items:
                if self.items[section]['sectionState'] == 'collapsed':
                    return 1 #если секция свернута - у нас в ней одна строка, само название секции и сумма за период
                elif self.items[section]['sectionState'] == 'expanded':
                    return len(self.items[section]['rows'])
            else:
                return 0

        def tableview_can_delete(self, tv, section, row):
            if self.items[section]['sectionState'] == 'collapsed' or self.items[section]['rows'][row]['rowName'] == 'Total:':
                return False
            else:
                return True

        def tableview_can_move(self, tv, section, row):
            return self.move_enabled

        def tableview_title_for_header(self, tv, section):
            if self.items[section]['sectionState'] == 'collapsed':
                return '' #при свернутой секции возвращаем пустую строку, тогда она не будет отображаться вообще, только ее первая и единственная строка
            elif self.items[section]['sectionState'] == 'expanded':
                return (self.items[section]['sectionName']+'\t('+str(self.items[section]['sectionSum'])+')')

        def tableview_title_for_footer(self, tv, section):
            return None

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

        def tableview_delete(self, tableview, section, row):
            # Called when the user confirms deletion of the given row.
            rowId = self.items[section]['rows'][row]['rowId']
            rowSum = self.items[section]['rows'][row]['rowSum']
            self.reload_disabled = True
            del self.items[section]['rows'][row]
            self.reload_disabled = False
            tableview.delete_rows([(row, section), ])
            if self.edit_action:
                self.edit_action(self, rowId, rowSum)

        def divideString(self, lenght, string):
            #делим длинную строку переносами строки.
            if len(string) > lenght:
                try:
                    indexToReplace = string.rindex(' ', 0, lenght) #вычисляем индекс последнего пробела в диапазоне 0-LENGHT
                    string = string[:indexToReplace]+ '\n' + self.divideString(lenght, string[indexToReplace+1:]) #заменяем его на символ переноса строки '\n', остаток строки еще раз рекурсивно засылаем в divideString()
                    return string
                except:
                    string = string[:lenght-3] + '...' #если пробелов в первых LENGHT-символов нет - заменяем последние 3 символа точками, остальное отбрасывем
                    return string
            else:
                return string

    class TitledListDataSource(ui.ListDataSource):
        #отличия от стандартного ui.ListDataSource:
        # -заголовок, который отображается как имя единственной секции
        # -ячейки не выделяются при выборе (cell.selectable=False)
        def __init__(self, items, title='', action=None, editAction=None, accessoryAction=None, deleteEnabled=False, moveEnabled=False):
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

            self.title = title
            self.items = items

            self.text_color = None
            self.highlight_color = None
            self.font = None #('<system>', 12)
            self.number_of_lines = 0 #uses as many lines, as needed to display a text

        def tableview_title_for_header(self, tv, section):
            return self.title
        
        def tableview_cell_for_row(self, tv, section, row):
            item = self.items[row]
            cell = ui.TableViewCell()
            cell.text_label.number_of_lines = self.number_of_lines
            cell.selectable = False
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

class Model(): #sqlite3 data access layer
    def __init__(self, controller):
        self.controller = controller
        if not os.path.isfile(DB):
            self.createDb()

    def createDb(self):
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        cur.execute('''CREATE TABLE IF NOT EXISTS purchases(
                            id INTEGER PRIMARY KEY,
                            name TEXT,
                            category TEXT,
                            price REAL,
                            date TEXT,
                            note TEXT)''')

        cur.execute('''CREATE TABLE IF NOT EXISTS categories(
                                    id INTEGER PRIMARY KEY,
                                    name TEXT)''')

        testDataCategories = [('Продукты', ),
                    ('Хозяйство', ),
                    ('Бытовая химия', ),
                    ('Анка', ),
                    ('Машина', ),
                    ('Фастфуд', ),
                    ('Бензин', ),
                    ('Долги', ),
                    ('Другое', ),
                    ('Жилье', ),
                    ('Здоровье', ),
                    ('Канцелярия', ),
                    ('Обед на работе', ),
                    ('Одежда', ),
                    ('Подарки', ),
                    ('Проезд', ),
                    ('Развлечения', ),
                    ('Саша', ),
                    ('Связь', ),
                    ('Списание', ),
                    ('Стрижка', )]

        cur.executemany('INSERT INTO categories (name) VALUES(?)', testDataCategories)
        conn.commit()
        conn.close()

    def getNow(self): #return local time datetime string '%Y-%m-%d %H:%M:%S'
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        now = db.execute('SELECT datetime("now", "localtime")').fetchone()[0]
        connection.close()
        return now

    def getTotalPriceFromPeriod(self, period):
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        total = db.execute('SELECT sum(price) FROM purchases WHERE date(date) BETWEEN ? AND ?', period).fetchone()[0]
        connection.close()
        return total

    def getTotalPriceFromAllTime(self):
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        total = db.execute('SELECT sum(price) FROM purchases').fetchone()[0]
        connection.close()
        return total
    
    def getTransactionsFromPeriod(self, period):
        connection = sqlite3.connect(DB)
        connection.row_factory = sqlite3.Row
        db = connection.cursor()
        #разделитель в виде '\t', т. к. по умолчанию разделитель ','. А в имени транзакции могут использоваться запятые, что приведет к неправильной интерпретации
        #подвыборка сделана для сортировки, т. к. внутри group_concat сортировку не сделать нормально
        transactions = db.execute('''SELECT category,
                            count(price) as numOfTransactions,
                            sum(price) as total,
                            group_concat(name, "\t") as names,
                            group_concat(price, "\t") as prices,
                            group_concat(date(date), "\t") as dates,
                            group_concat(id, "\t") as ids
                            FROM (SELECT id,
                                        category,
                                        name,
                                        price,
                                        date FROM purchases
                                        WHERE date(date) BETWEEN ? AND ?
                                        ORDER BY date DESC)
                            GROUP BY category
                            ORDER BY sum(price) DESC''', period).fetchall()    
        connection.close()
        return transactions

    def getTransactionsFromAllTime(self, period):
        #разделитель в виде '\t', т. к. по умолчанию разделитель ','. А в имени транзакции могут использоваться запятые, что приведет к неправильной интерпретации
        #добавлен пустой входной параметр period для удобства и совместимости в Controller.getItemsForMainTable()
        connection = sqlite3.connect(DB)
        connection.row_factory = sqlite3.Row
        db = connection.cursor()
        transactions = db.execute('''SELECT category,
                            count(price) as numOfTransactions,
                            sum(price) as total,
                            group_concat(name, "\t") as names,
                            group_concat(price, "\t") as prices,
                            group_concat(date(date), "\t") as dates,
                            group_concat(id, "\t") as ids
                            FROM (SELECT id,
                                        category,
                                        name,
                                        price,
                                        date FROM purchases
                                        ORDER BY date DESC)
                            GROUP BY category
                            ORDER BY sum(price) DESC''').fetchall()
        connection.close()
        return transactions

    def getCategories(self):
        connection = sqlite3.connect(DB)
        connection.row_factory = lambda cursor, row: row[0] #эта магия позволяет возвращать из db список, а не список кортежей, то есть возвращает нулевой элемент каждого кортежа
        db = connection.cursor()
        categories = db.execute('SELECT name FROM categories ORDER BY id').fetchall()
        connection.close()
        return categories

    def getTransaction(self, rowId):
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        transaction = db.execute('SELECT id, name, category, price, date, note FROM purchases WHERE id = ?', (rowId, )).fetchone()
        connection.close()
        return transaction

    def updateTransaction(self, transactionData):
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        db.execute('UPDATE purchases SET name=?, category=?, price=?, date=?, note=? WHERE id=?', (transactionData['name'], transactionData['category'], transactionData['price'], transactionData['date'], transactionData['note'], transactionData['id']))
        connection.commit()
        connection.close()

    def addTransaction(self, transactionData):
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        db.execute('INSERT INTO purchases (name, category, price, date, note) VALUES(?, ?, ?, ?, ?)', (transactionData['name'], transactionData['category'], transactionData['price'], transactionData['date'], transactionData['note']))
        connection.commit()
        connection.close()

    def deleteTransaction(self, transactionId):
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        db.execute('DELETE FROM purchases WHERE id = ?', (transactionId, ))
        connection.commit()
        connection.close()

class Controller():
    def __init__(self):
        self.model = Model(self)
        self.gui = GUI(self)

        self.mode = INITIALMODE
        self.date = self.getNow() #datetime object
        self.fromDate = None #datetime object
        self.toDate = None #datetime object
        
        self.gui.update(self.getNameForMainTable(), self.getItemsForMainTable())

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
        self.gui.update(self.getNameForMainTable(), self.getItemsForMainTable())     

    def calendarButtonAction(self, result):
        self.date = result
        self.gui.update(self.getNameForMainTable(), self.getItemsForMainTable())

    def settingsButtonAction(self):
        print('settingsButtonAction')

    def searchButtonAction(self):
        print('searchButtonAction')

    def addButtonAction(self, result):
        if result['id'] and result['category'] and result['price']: #режим редактирования транзакции, т. к. есть id, будем ее перезаписывать по этому id
            self.model.updateTransaction(result)
        elif result['category'] and result['price']: #режим добавления транзакции, т. к. нет id
            if not result['date']:
                result['date'] = str(self.getNow())
            if not result['note']:
                result['note'] = ''
            self.model.addTransaction(result)
        else:
            raise ValueError('В транзакции отсутствует обязательное(ые) поле(я). Category и/или Price')

    def mainTableRowDeletedAction(self, sender, rowId, rowSum):
        sender.items[sender.selected_section]['rows'][0]['rowSum'] -= 1 #0 строка - Total
        sender.items[sender.selected_section]['sectionSum'] = self.floatToPrice(self.priceToFloat(sender.items[sender.selected_section]['sectionSum']) - self.priceToFloat(rowSum))
        if sender.items[sender.selected_section]['sectionSum'] == '0': #удаляем секцию, если в ней нет транзакций
            del sender.items[sender.selected_section]
        self.model.deleteTransaction(rowId)

    def mainTableRowAccessoryTapedAction(self, sender):
        @ui.in_background
        def showTransaction(title, result):
            a = console.alert(title=title, message=result, button1='Copy', button2='Ok', hide_cancel_button=True)
            if a == 1:
                clipboard.set(result)

        rowId = sender.items[sender.tapped_accessory_section]['rows'][sender.tapped_accessory_row]['rowId']
        res = self.getTransaction(rowId)
        title = 'Transaction data'
        fullRes = 'ID: '+str(res['id'])+'\nName: '+res['name']+'\nCategory: '+res['category']+'\nPrice: '+str(res['price'])+'\nDate: '+res['date']+'\nNote: '+res['note']

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

    def floatToPrice(self, fPrice, mode='rough'):
        if fPrice == None:
            return '0 ₽'
        elif mode == 'rough':
            return (format(fPrice, ',.0f').replace(',', '  ')+CURRENCYSYMBOL)
        elif mode == 'precisely':
            return (format(fPrice, ',.2f').replace(',', '  ')+CURRENCYSYMBOL)
        else:
            raise ValueError('mode: несоответствующее значение')

    def priceToFloat(self, price):
        if price == None:
            return 0.0
        else:
            return (float(price[0:-2].replace(' ', '')))
    
    def getNow(self): #return datetime object
        now = self.model.getNow()
        return datetime.datetime.strptime(now, '%Y-%m-%d %H:%M:%S')

    def getTheme(self):
        return ui.get_ui_style()

    def getNameForMainTable(self):
        if self.mode == 'D':
            period = (self.date.strftime('%Y-%m-%d'), self.date.strftime('%Y-%m-%d'))
            total = self.model.getTotalPriceFromPeriod(period)
            return (self.date.strftime(LOCALDATEFORMATDAY)+' ('+self.floatToPrice(total)+')')
        elif self.mode == 'M':
            period = ((self.date.strftime('%Y-%m')+'-01'), (self.date.strftime('%Y-%m')+'-31'))
            total = self.model.getTotalPriceFromPeriod(period)
            return (self.date.strftime(LOCALDATEFORMATMONTH)+' ('+self.floatToPrice(total)+')')
        elif self.mode == 'Y':
            period = ((self.date.strftime('%Y')+'-01-01'), (self.date.strftime('%Y')+'-12-31'))
            total = self.model.getTotalPriceFromPeriod(period)
            return (self.date.strftime(LOCALDATEFORMATYEAR)+' ('+self.floatToPrice(total)+')')
        elif self.mode == 'P':
            period = (self.fromDate.strftime('%Y-%m-%d'), self.toDate.strftime('%Y-%m-%d'))
            total = self.model.getTotalPriceFromPeriod(period)
            return (self.fromDate.strftime(LOCALDATEFORMATDAY)+' - '+self.toDate.strftime(LOCALDATEFORMATDAY)+' ('+self.floatToPrice(total)+')')
        elif self.mode == 'All':
            total = self.model.getTotalPriceFromAllTime()
            return ('All'+' ('+self.floatToPrice(total)+')')
        else:
            raise ValueError('Несоответствующее значение')

    def getItemsForMainTable(self):
        if self.mode == 'D':
            period = (self.date.strftime('%Y-%m-%d'), self.date.strftime('%Y-%m-%d'))
            getTransaction = self.model.getTransactionsFromPeriod
        elif self.mode == 'M':
            period = ((self.date.strftime('%Y-%m')+'-01'), (self.date.strftime('%Y-%m')+'-31'))
            getTransaction = self.model.getTransactionsFromPeriod
        elif self.mode == 'Y':
            period = ((self.date.strftime('%Y')+'-01-01'), (self.date.strftime('%Y')+'-12-31'))
            getTransaction = self.model.getTransactionsFromPeriod
        elif self.mode == 'P':
            period = (self.fromDate.strftime('%Y-%m-%d'), self.toDate.strftime('%Y-%m-%d'))
            getTransaction = self.model.getTransactionsFromPeriod
        elif self.mode == 'All':
            period = None
            getTransaction = self.model.getTransactionsFromAllTime
        else:
            raise ValueError('Несоответствующее значение')

        transactions = getTransaction(period)
        result = []
        for row in transactions:
            string = {}
            string['sectionState'] = 'collapsed'
            string['sectionName'] = row['category']
            string['sectionSum'] = self.floatToPrice(float(row['total']))
            string['rows'] = [{'rowId':None, 'rowDate':None, 'rowName':'Total:', 'rowSum':row['numOfTransactions']}, ]
            for i in range(row['numOfTransactions']):
                #разделитель в виде '\t', т. к. по умолчанию разделитель ','. А в имени транзакции могут использоваться запятые, что приведет к неправильной интерпретации
                r = {'rowId':row['ids'].split('\t')[i],
                    'rowDate':datetime.datetime.strptime(row['dates'].split('\t')[i], DEFAULTDATEFORMATDAY).strftime(LOCALDATEFORMATDAY), #меняем дату под локаль
                    'rowName':row['names'].split('\t')[i],
                    'rowSum':self.floatToPrice(float(row['prices'].split('\t')[i]))}
                string['rows'].append(r)
            result.append(string)
        return result

    def getCategories(self):
        return self.model.getCategories()

    def getTransaction(self, rowId):
        rawData = self.model.getTransaction(rowId)
        transactionData = {'id':rawData[0], 'name':rawData[1], 'category':rawData[2], 'price':rawData[3], 'date':rawData[4], 'note':rawData[5]}
        return transactionData

    def addFastTransaction(self):
        #adding transaction from iOS shortcuts
        self.gui._addButtonAction(None)

    def vibrate(self):
        c = ctypes.CDLL(None)
        p = c.AudioServicesPlaySystemSound
        p.restype, p.argtypes = None, [ctypes.c_int32]
        vibrate_id = 0x00000fff
        p(vibrate_id)

controller = Controller()
if len(sys.argv) > 1:
    if sys.argv[1] == 'addTransaction':
        controller.addFastTransaction()
    elif sys.argv[1] == 'start':
        pass #обычный запуск без доп действий
