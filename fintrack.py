import sys, ui, dialogs, os, sqlite3, datetime, console, clipboard, collections

DB = '/private/var/mobile/Library/Mobile Documents/iCloud~com~omz-software~Pythonista3/Documents/FinTrack/fintrack.db' #sqlite3 db
DEFAULTFORMATDAY = '%Y-%m-%d' #defaul date format from sqlite3
TABLECELLLENGHT = 30 #количесвто символов, которое помещается в одной строке таблицы (когда категория открыта), зависит от размера шрифта SMALLFONT
SMALLFONT = ('<system>', 14) #размер шрифта в таблице в открытой категории (он меньше чем шрифт самой категории)

DEFAULTCATEGORIES = 'Food\tCinema\tCar'
INITIALMODE = 'Month' #режим, в котором стартует приложение по умолчанию, D = Date, M = Month, Y = Year, A = All time
CURRENCYSYMBOL =  '₽'
LOCALDATEFORMAT = {'Europe':{'day':'%d.%m.%Y', 'month':'%B %Y', 'year':'%Y', 'short':'%d.%m.%y'},
                    'Japan':{'day':'%Y.%m.%d', 'month':'%B %Y', 'year':'%Y', 'short':'%y.%m.%d'},
                    'USA':{'day':'%m/%d/%Y', 'month':'%B %Y', 'year':'%Y', 'short':'%m/%d/%y'}}
DEFAULTSETTINGSID = 0
USERSETTINGSID = 1

CALENDAR = 'calendar36.png'
PERIOD = 'period36.png'
ADD = 'plus36.png'
SEARCH = 'search36.png'
SETTINGS = 'settings36.png'

class GUI():
    def __init__(self, controller):
        self.controller = controller

        self.result = None #тут хранится результат того или иного взаимодейсвтия с gui, который будет потом передан в соответствующий метод logic

        self.periodButton = ui.Button(image=ui.Image.named(PERIOD),
            action=self.periodButtonAction,
            alpha=0.0)
        self.calendarButton = ui.Button(image=ui.Image.named(CALENDAR),
            action=self.calendarButtonAction,
            alpha=0.0)
        self.settingsButton = ui.Button(image=ui.Image.named(SETTINGS),
            action=self.settingsButtonAction,
            alpha=0.0)
        self.searchButton = ui.Button(image=ui.Image.named(SEARCH),
            action=self.searchButtonAction,
            alpha=0.0)
        self.addButton = ui.Button(image=ui.Image.named(ADD),
            action=self.addButtonAction,
            alpha=0.0)
        self.mainTableDataSource = self.DbListDataSource(items=None,
            action=self.mainTableRowSelectedAction,
            editAction=self.mainTableRowDeletedAction,
            accessoryAction=self.mainTableRowAccessoryTapedAction)
        self.mainTable = ui.TableView(data_source=self.mainTableDataSource,
            delegate=self.mainTableDataSource,
            editing = False,
            alpha=0.0)

        self.view = self.MyView(name='',
            flex='WH',
            background_color='white')

        self.view.add_subview(self.periodButton)
        self.view.add_subview(self.calendarButton)
        self.view.add_subview(self.settingsButton)
        self.view.add_subview(self.searchButton)
        self.view.add_subview(self.addButton)
        self.view.add_subview(self.mainTable)

        self.view.present(hide_close_button=False, style='popover', orientations=['portrait'])
        
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

        def present():    
            self.periodButton.alpha = 1.0
            self.calendarButton.alpha = 1.0
            self.settingsButton.alpha = 1.0
            self.searchButton.alpha = 1.0
            self.addButton.alpha = 1.0
            self.mainTable.alpha = 1.0
        ui.animate(present)

    @ui.in_background
    def periodButtonAction(self, sender):
        a = dialogs.list_dialog(title='Period?', items=('Day', 'Month', 'Year', 'All time', 'Custom period'), multiple=False)
        if a:
            if a == 'All time':
                self.calendarButton.enabled = False
                self.result = {'mode':a}
            elif a == 'Custom period':
                self.calendarButton.enabled = False
                fields = [{'type':'date', 'title':'From date:\t', 'key':'fromDate'},
                            {'type':'date', 'title':'To date:\t', 'key':'toDate'}]
                dates = dialogs.form_dialog(title='Choose period', fields=fields)
                if dates:
                    self.result = {'mode':a, 'fromDate':dates['fromDate'], 'toDate':dates['toDate']}
                else:
                    self.result = {'mode':self.controller.settings['initialMode']}
                    self.calendarButton.enabled = True
            else:
                self.calendarButton.enabled = True
                self.result = {'mode':a}
            self.controller.periodButtonAction(self.result)

    @ui.in_background
    def calendarButtonAction(self, sender):
        self.result = dialogs.date_dialog(title='Choose date')
        if self.result:
            self.controller.calendarButtonAction(self.result)

    @ui.in_background
    def settingsButtonAction(self, sender):
        initialMode = [{'type':'check', 'title':'Day', 'group':'initialMode', 'value':True if self.controller.settings['initialMode'] == 'Day' else False},
                        {'type':'check', 'title':'Month', 'group':'initialMode', 'value':True if self.controller.settings['initialMode'] == 'Month' else False},
                        {'type':'check', 'title':'Year', 'group':'initialMode', 'value':True if self.controller.settings['initialMode'] == 'Year' else False},
                        {'type':'check', 'title':'All time', 'group':'initialMode', 'value':True if self.controller.settings['initialMode'] == 'All time' else False}]
        
        dateFormats = [{'type':'check', 'title':'Europe', 'group':'localDateFormat', 'value':True if self.controller.settings['localDateFormat'] == 'Europe' else False},
                        {'type':'check', 'title':'Japan', 'group':'localDateFormat', 'value':True if self.controller.settings['localDateFormat'] == 'Japan' else False},
                        {'type':'check', 'title':'USA', 'group':'localDateFormat', 'value':True if self.controller.settings['localDateFormat'] == 'USA' else False}]

        currencySymbol = [{'type':'text', 'title':'Currency symbol:\t', 'key':'currencySymbol', 'value':self.controller.settings['currencySymbol']}]
        
        categories = []
        for i in self.controller.settings['categories']:
            a = {'title':i, 'group':'categories'}
            categories.append(a)
        
        addCategory = [{'type':'text', 'title':'New category name:\t', 'key':'newCategory'}]

        resetToDefaultSettings = [{'type':'switch', 'title':'Reset to default settings', 'key':'reset'}]
        
        items = [('Start mode:', initialMode),
                ('Local date formats:', dateFormats),
                ('Currency symbol:', currencySymbol),
                ('Categories:', categories),
                ('Add new category:', addCategory),
                ('Reset to default settings (except categories):', resetToDefaultSettings)]

        settings = self.settings_dialog(title='Settings', sections=items)
        if settings:
            self.controller.settingsButtonAction(settings)

    @ui.in_background
    def searchButtonAction(self, sender):
        if self.searchButtonAction:
            self.searchButtonAction(self.result)

    @ui.in_background
    def addButtonAction(self, sender, transactionData=None):
        if transactionData: #если редактируем существующую транзакцию
            transactionId = transactionData['id']
            mainData = [{'type':'number', 'title':'Price:\t', 'key':'price', 'value':str(transactionData['price'])},
                {'type':'text', 'title':'Name:\t', 'key':'name', 'value':transactionData['name']},
                {'type':'date', 'title':'Date:\t', 'key':'date', 'value':datetime.datetime.strptime(transactionData['date'], '%Y-%m-%d %H:%M:%S')},
                {'type':'text', 'title':'Note:\t', 'key':'note', 'value':transactionData['note']}]
        else: #если создаем новую транзакцию
            transactionId = None
            mainData = [{'type':'number', 'title':'Price:\t', 'key':'price'},
                {'type':'text', 'title':'Name:\t', 'key':'name'},
                {'type':'date', 'title':'Date:\t', 'key':'date'},
                {'type':'text', 'title':'Note:\t', 'key':'note'}]

        categories = []
        for i in self.controller.settings['categories']:
            a = {'type':'check', 'title':i, 'group':'category'}
            categories.append(a)
        categories.append({'type':'text', 'title':'New category name:\t', 'key':'newCategory'}) #в конце добавляем textField для ввода новой категории

        items = [('Price, name, date?', mainData), ('Category?', categories)]

        tfSteps = ['price', 'name'] #порядок активации textField'ов в авторежиме по нажатию кнопки enter на клавиатуре, key-параметры строк в таблице

        transaction = self.transaction_dialog(title='Add transaction', sections=items, tfSteps=tfSteps)
        if transaction:
            self.controller.addButtonAction(transaction, transactionId)
            self.update(self.controller.getNameForMainTable(), self.controller.getItemsForMainTable())

    def mainTableRowSelectedAction(self, sender):
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
            self.addButtonAction(None, transactionData)

    def mainTableRowDeletedAction(self, sender, rowId, rowSum):
        self.controller.mainTableRowDeletedAction(sender, rowId, rowSum)
        sender.reload()

    def mainTableRowAccessoryTapedAction(self, sender):
        self.result = sender
        self.controller.mainTableRowAccessoryTapedAction(self.result)

    def deleteRows(self, rowsToDelete):
        self.mainTable.delete_rows(rowsToDelete)

    def update(self, name, tableItems):
        self.view.name = name
        self.mainTableDataSource.items = tableItems
        self.mainTable.reload()

    def transaction_dialog(self, title='', fields=None, sections=None, done_button_title='Done', tfSteps=None):
        #from dialogs
        if not sections and not fields:
            raise ValueError('sections or fields are required')
        if not sections:
            sections = [('', fields)]
        if not isinstance(title, str):
            raise TypeError('title must be a string')
        for section in sections:
            if not isinstance(section, collections.Sequence):
                raise TypeError('Sections must be sequences (title, fields)')
            if len(section) < 2:
                raise TypeError('Sections must have 2 or 3 items (title, fields[, footer]')
            if not isinstance(section[0], str):
                raise TypeError('Section titles must be strings')
            if not isinstance(section[1], collections.Sequence):
                raise TypeError('Expected a sequence of field dicts')
            for field in section[1]:
                if not isinstance(field, dict):
                    raise TypeError('fields must be dicts')

        c = self.TransactionDialogController(title, sections, done_button_title=done_button_title, tfSteps=tfSteps)
        c.container_view.present()

        c.view[tfSteps[0]].content_view[tfSteps[0]].begin_editing() #смотри TransactionDialogController.textfield_should_return
        c.container_view.wait_modal()
        # Get rid of the view to avoid a retain cycle:
        c.container_view = None
        if c.was_canceled:
            return None
        else:
            return c.values
    
    def settings_dialog(self, title='', fields=None, sections=None, done_button_title='Done'):
        #from dialogs
        if not sections and not fields:
            raise ValueError('sections or fields are required')
        if not sections:
            sections = [('', fields)]
        if not isinstance(title, str):
            raise TypeError('title must be a string')
        for section in sections:
            if not isinstance(section, collections.Sequence):
                raise TypeError('Sections must be sequences (title, fields)')
            if len(section) < 2:
                raise TypeError('Sections must have 2 or 3 items (title, fields[, footer]')
            if not isinstance(section[0], str):
                raise TypeError('Section titles must be strings')
            if not isinstance(section[1], collections.Sequence):
                raise TypeError('Expected a sequence of field dicts')
            for field in section[1]:
                if not isinstance(field, dict):
                    raise TypeError('fields must be dicts')

        c = self.SettingsDialogController(title, sections, done_button_title=done_button_title)
        c.container_view.present()
        c.container_view.wait_modal()
        # Get rid of the view to avoid a retain cycle:
        c.container_view = None
        if c.was_canceled:
            return None
        else:
            return c.values
    
    class TransactionDialogController ():
        #from dialogs
        def __init__(self, title, sections, done_button_title='Done', tfSteps=None):
            self.was_canceled = True
            self.shield_view = None
            self.values = {}
            self.container_view = GUI.FormContainerView()
            self.container_view.frame = (0, 0, 500, 500)
            self.container_view.delegate = self
            self.view = ui.TableView('grouped')
            self.view.flex = 'WH'
            self.container_view.add_subview(self.view)
            self.container_view.name = title
            self.view.frame = (0, 0, 500, 500)
            self.view.data_source = self
            self.view.delegate = self
            self.cells = []

            self.offset = (0, 240) #позиция на которую скроллится view при нажатии Enter в последнем textField'е. Переходим сразу ниже к категориям
            self.tfSteps = tfSteps #порядок активации textField'ов в авторежиме по нажатию кнопки enter на клавиатуре, key-параметры строк в таблице

            self.sections = sections
            
            for section in self.sections:
                section_cells = []
                self.cells.append(section_cells)
                items = section[1]
                for i, item in enumerate(items):
                    cell = ui.TableViewCell('value1')
                    cell.name = item.get('key', None) #добавляем имя для ячейки, для дальнейшей идентификации
                    icon = item.get('icon', None)
                    tint_color = item.get('tint_color', None)
                    if tint_color:
                        cell.tint_color = tint_color
                    if icon:
                        if isinstance(icon, str):
                            icon = ui.Image.named(icon)
                        if tint_color:
                            cell.image_view.image = icon.with_rendering_mode(ui.RENDERING_MODE_TEMPLATE)
                        else:
                            cell.image_view.image = icon
                        
                    title_color = item.get('title_color', None)
                    if title_color:
                        cell.text_label.text_color = title_color
                    
                    t = item.get('type', None)
                    key = item.get('key', item.get('title', str(i)))
                    item['key'] = key
                    title = item.get('title', '')
                    if t == 'switch':
                        value = item.get('value', False)
                        self.values[key] = value
                        cell.text_label.text = title
                        cell.selectable = False
                        switch = ui.Switch()
                        w, h = cell.content_view.width, cell.content_view.height
                        switch.center = (w - switch.width/2 - 10, h/2)
                        switch.flex = 'TBL'
                        switch.value = value
                        switch.name = key
                        switch.action = self.switch_action
                        if tint_color:
                            switch.tint_color = tint_color
                        cell.content_view.add_subview(switch)
                    elif t == 'text' or t == 'url' or t == 'email' or t == 'password' or t == 'number':
                        value = item.get('value', '')
                        self.values[key] = value
                        placeholder = item.get('placeholder', '')
                        cell.selectable = False
                        cell.text_label.text = title
                        label_width = ui.measure_string(title, font=cell.text_label.font)[0]
                        if cell.image_view.image:
                            label_width += min(64, cell.image_view.image.size[0] + 16)
                        cell_width, cell_height = cell.content_view.width, cell.content_view.height
                        tf = ui.TextField()
                        tf_width = max(40, cell_width - label_width - 32)
                        tf.frame = (cell_width - tf_width - 8, 1, tf_width, cell_height-2)
                        tf.bordered = False
                        tf.placeholder = placeholder
                        tf.flex = 'W'
                        tf.text = value
                        tf.text_color = '#337097'
                        if t == 'text':
                            tf.autocorrection_type = item.get('autocorrection', None)
                            tf.autocapitalization_type = item.get('autocapitalization', ui.AUTOCAPITALIZE_SENTENCES)
                            tf.spellchecking_type = item.get('spellchecking', None)
                        if t == 'url':
                            tf.keyboard_type = ui.KEYBOARD_URL
                            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
                            tf.autocorrection_type = False
                            tf.spellchecking_type = False
                        elif t == 'email':
                            tf.keyboard_type = ui.KEYBOARD_EMAIL
                            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
                            tf.autocorrection_type = False
                            tf.spellchecking_type = False
                        elif t == 'number':
                            tf.keyboard_type = ui.KEYBOARD_NUMBERS
                            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
                            tf.autocorrection_type = False
                            tf.spellchecking_type = False
                        elif t == 'password':
                            tf.secure = True
                        
                        tf.clear_button_mode = 'while_editing'
                        tf.name = key
                        tf.delegate = self
                        cell.content_view.add_subview(tf)

                    elif t == 'check':
                        value = item.get('value', False)
                        group = item.get('group', None)
                        if value:
                            cell.accessory_type = 'checkmark'
                            cell.text_label.text_color = cell.tint_color
                        cell.text_label.text = title
                        if group:
                            if value:
                                self.values[group] = key
                        else:
                            self.values[key] = value
                    elif t == 'date' or t == 'datetime' or t == 'time':
                        value = item.get('value', datetime.datetime.now())
                        if type(value) == datetime.date:
                            value = datetime.datetime.combine(value, datetime.time())
                        if type(value) == datetime.time:
                            value = datetime.datetime.combine(value, datetime.date.today())
                        date_format = item.get('format', None)
                        if not date_format:
                            if t == 'date':
                                date_format = '%Y-%m-%d'
                            elif t == 'time':
                                date_format = '%H:%M'
                            else:
                                date_format = '%Y-%m-%d %H:%M'
                        item['format'] = date_format
                        cell.detail_text_label.text = value.strftime(date_format)
                        self.values[key] = value
                        cell.text_label.text = title
                    else:
                        cell.selectable = False
                        cell.text_label.text = item.get('title', '')

                    section_cells.append(cell)
            
            done_button = ui.ButtonItem(title=done_button_title)
            done_button.action = self.done_action
            self.container_view.right_button_items = [done_button]
        
        def update_kb_height(self, h):
            self.view.content_inset = (0, 0, h, 0)
            self.view.scroll_indicator_insets = (0, 0, h, 0)
        
        def tableview_number_of_sections(self, tv):
            return len(self.cells)
        
        def tableview_title_for_header(self, tv, section):
            return self.sections[section][0]

        def tableview_title_for_footer(self, tv, section):
            s = self.sections[section]
            if len(s) > 2:
                return s[2]
            return None
        
        def tableview_number_of_rows(self, tv, section):
            return len(self.cells[section])
        
        def tableview_did_select(self, tv, section, row):
            sel_item = self.sections[section][1][row]
            t = sel_item.get('type', None)
            if t == 'check':
                key = sel_item['key']
                tv.selected_row = -1
                group = sel_item.get('group', None)
                cell = self.cells[section][row]
                if group:
                    for i, s in enumerate(self.sections):
                        for j, item in enumerate(s[1]):
                            if item.get('type', None) == 'check' and item.get('group', None) == group and item is not sel_item:
                                self.cells[i][j].accessory_type = 'none'
                                self.cells[i][j].text_label.text_color = None
                    cell.accessory_type = 'checkmark'
                    cell.text_label.text_color = cell.tint_color
                    self.values[group] = key
                else:
                    if cell.accessory_type == 'checkmark':
                        cell.accessory_type = 'none'
                        cell.text_label.text_color = None
                        self.values[key] = False
                    else:
                        cell.accessory_type = 'checkmark'
                        self.values[key] = True
                if self.values['price'] != '' and (self.values.get('category', None) or self.values['newCategory'] != ''):
                    self.done_action(None)
            elif t == 'date' or t == 'time' or t == 'datetime':
                tv.selected_row = -1
                self.selected_date_key = sel_item['key']
                self.selected_date_value = self.values.get(self.selected_date_key)
                self.selected_date_cell = self.cells[section][row]
                self.selected_date_format = sel_item['format']
                self.selected_date_type = t
                if t == 'date':
                    mode = ui.DATE_PICKER_MODE_DATE
                elif t == 'time':
                    mode = ui.DATE_PICKER_MODE_TIME
                else:
                    mode = ui.DATE_PICKER_MODE_DATE_AND_TIME
                self.show_datepicker(mode)

        def tableview_can_delete(self, tv, section, row):
            '''if self.sections[section][0] == 'Category?':
                return True
            else:
                return False'''
            return False

        def tableview_can_move(self, tv, section, row):
            '''if self.sections[section][0] == 'Category?':
                return True
            else:
                return False'''
            return False

        def tableview_move_row(self, tv, from_section, from_row, to_section, to_row):
            '''self.cells[from_section][from_row], self.cells[to_section][to_row] = self.cells[to_section][to_row], self.cells[from_section][from_row]
            self.categoriesWasChanged = True
            self.newCategories = []
            for i in self.cells[from_section]:
                self.newCategories.append(i.text_label.text)'''
            pass
                    
        def tableview_delete(self, tv, section, row):
            '''del self.cells[section][row]
            tv.delete_rows([(row, section), ])
            self.newCategories = []
            for i in self.cells[section]:
                self.newCategories.append(i.text_label.text)'''
            pass
            
        def show_datepicker(self, mode):
            ui.end_editing()
            self.shield_view = ui.View()
            self.shield_view.flex = 'WH'
            self.shield_view.frame = (0, 0, self.view.width, self.view.height)
            
            self.dismiss_datepicker_button = ui.Button()
            self.dismiss_datepicker_button.flex = 'WH'
            self.dismiss_datepicker_button.frame = (0, 0, self.view.width, self.view.height)
            self.dismiss_datepicker_button.background_color = (0, 0, 0, 0.5)
            self.dismiss_datepicker_button.action = self.dismiss_datepicker
            self.dismiss_datepicker_button.alpha = 0.0
            self.shield_view.add_subview(self.dismiss_datepicker_button)

            self.date_picker = ui.DatePicker()
            self.date_picker.date = self.selected_date_value
            self.date_picker.background_color = 'white'
            self.date_picker.mode = mode
            self.date_picker.frame = (0, self.shield_view.height - self.date_picker.height, self.shield_view.width, self.date_picker.height)
            self.date_picker.flex = 'TW'
            self.date_picker.transform = ui.Transform.translation(0, self.date_picker.height)
            self.shield_view.add_subview(self.date_picker)

            self.container_view.add_subview(self.shield_view)
            
            def fade_in():
                self.dismiss_datepicker_button.alpha = 1.0
                self.date_picker.transform = ui.Transform.translation(0, 0)
            ui.animate(fade_in, 0.3)

        def dismiss_datepicker(self, sender):
            value = self.date_picker.date
            
            if self.selected_date_type == 'date':
                self.selected_date_cell.detail_text_label.text = value.strftime(self.selected_date_format)
            elif self.selected_date_type == 'time':
                self.selected_date_cell.detail_text_label.text = value.strftime(self.selected_date_format)
            else:
                self.selected_date_cell.detail_text_label.text = value.strftime(self.selected_date_format)

            self.values[self.selected_date_key] = value
            
            def fade_out():
                self.dismiss_datepicker_button.alpha = 0.0
                self.date_picker.transform = ui.Transform.translation(0, self.date_picker.height)
            def remove():
                self.container_view.remove_subview(self.shield_view)
                self.shield_view = None
            ui.animate(fade_out, 0.3, completion=remove)
        
        def tableview_cell_for_row(self, tv, section, row):
            return self.cells[section][row]
        
        def textfield_did_change(self, tf):
            self.values[tf.name] = tf.text

        def textfield_did_end_editing(self, tf):
            pass

        def textfield_should_return(self, tf):
            tf.end_editing()
            try:
                self.tfSteps.remove(tf.name) #пытаемся удалить tf из списка tfSteps, если он там есть - удаляем, если нет - ничего не делаем
            except:
                return #если tf не в списке tfSteps - не делаем ничего
            if len(self.tfSteps) == 0: #прошагали по всем tf из tfSteps - скроллим на выбор категории
                def scroll():
                        self.view.content_offset = (self.offset)
                ui.animate(scroll)
            else:
                a = self.tfSteps[0] #имя следующего tf, а так же и имя TableViewCell
                b = self.view[a] #TableViewCell, обращаемся к subviews по имени. superView - self.view, то есть TableView
                c = b.content_view[a] #textField, обращаемся к subViews по имени. superView - TableViewCell
                c.begin_editing()

        def switch_action(self, sender):
            self.values[sender.name] = sender.value
        
        def done_action(self, sender):
            try:
                self.values['price'] = float(self.values['price'])
                if self.values.get('category', None) or self.values['newCategory'] != '':
                    if self.shield_view:
                        self.dismiss_datepicker(None)
                    else:
                        ui.end_editing()
                        self.was_canceled = False
                        self.container_view.close()
            except:
                pass

    class FormContainerView(ui.View):
            #from dialogs
            def __init__(self):
                self.delegate = None
                
            def keyboard_frame_will_change(self, f):
                r = ui.convert_rect(f, to_view=self)
                if r[3] > 0:
                    kbh = self.height - r[1]
                else:
                    kbh = 0
                if self.delegate:
                    self.delegate.update_kb_height(kbh)

    class SettingsDialogController(TransactionDialogController):
        #from dialogs
        def __init__(self, title, sections, done_button_title='Done'):
            self.was_canceled = True
            self.shield_view = None
            self.values = {}
            self.container_view = GUI.FormContainerView()
            self.container_view.frame = (0, 0, 500, 500)
            self.container_view.delegate = self
            self.view = ui.TableView('grouped')
            self.view.flex = 'WH'
            self.container_view.add_subview(self.view)
            self.container_view.name = title
            self.view.frame = (0, 0, 500, 500)
            self.view.data_source = self
            self.view.delegate = self
            self.cells = []

            self.view.editing = True
            self.view.allows_selection_during_editing = True
            self.newCategories = []

            self.sections = sections
                        
            self.createCells()

            done_button = ui.ButtonItem(title=done_button_title)
            done_button.action = self.done_action
            self.container_view.right_button_items = [done_button]

        def createCells(self):
            self.cells = [] #очищаю список, т. к. данная функция вызывается не только при ините, но и при добавлении новой категории
            for section in self.sections:
                section_cells = []
                self.cells.append(section_cells)
                items = section[1]
                for i, item in enumerate(items):
                    cell = ui.TableViewCell('value1')
                    cell.name = item.get('key', None) #добавляем имя для ячейки, для дальнейшей идентификации
                    icon = item.get('icon', None)
                    tint_color = item.get('tint_color', None)
                    if tint_color:
                        cell.tint_color = tint_color
                    if icon:
                        if isinstance(icon, str):
                            icon = ui.Image.named(icon)
                        if tint_color:
                            cell.image_view.image = icon.with_rendering_mode(ui.RENDERING_MODE_TEMPLATE)
                        else:
                            cell.image_view.image = icon
                        
                    title_color = item.get('title_color', None)
                    if title_color:
                        cell.text_label.text_color = title_color
                    
                    t = item.get('type', None)
                    key = item.get('key', item.get('title', str(i)))
                    item['key'] = key
                    title = item.get('title', '')
                    if t == 'switch':
                        value = item.get('value', False)
                        self.values[key] = value
                        cell.text_label.text = title
                        cell.selectable = False
                        switch = ui.Switch()
                        w, h = cell.content_view.width, cell.content_view.height
                        switch.center = (w - switch.width/2 - 10, h/2)
                        switch.flex = 'TBL'
                        switch.value = value
                        switch.name = key
                        switch.action = self.switch_action
                        if tint_color:
                            switch.tint_color = tint_color
                        cell.content_view.add_subview(switch)
                    elif t == 'text' or t == 'url' or t == 'email' or t == 'password' or t == 'number':
                        value = item.get('value', '')
                        self.values[key] = value
                        placeholder = item.get('placeholder', '')
                        cell.selectable = False
                        cell.text_label.text = title
                        label_width = ui.measure_string(title, font=cell.text_label.font)[0]
                        if cell.image_view.image:
                            label_width += min(64, cell.image_view.image.size[0] + 16)
                        cell_width, cell_height = cell.content_view.width, cell.content_view.height
                        tf = ui.TextField()
                        tf_width = max(40, cell_width - label_width - 32)
                        tf.frame = (cell_width - tf_width - 8, 1, tf_width, cell_height-2)
                        tf.bordered = False
                        tf.placeholder = placeholder
                        tf.flex = 'W'
                        tf.text = value
                        tf.text_color = '#337097'
                        if t == 'text':
                            tf.autocorrection_type = item.get('autocorrection', None)
                            tf.autocapitalization_type = item.get('autocapitalization', ui.AUTOCAPITALIZE_SENTENCES)
                            tf.spellchecking_type = item.get('spellchecking', None)
                        if t == 'url':
                            tf.keyboard_type = ui.KEYBOARD_URL
                            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
                            tf.autocorrection_type = False
                            tf.spellchecking_type = False
                        elif t == 'email':
                            tf.keyboard_type = ui.KEYBOARD_EMAIL
                            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
                            tf.autocorrection_type = False
                            tf.spellchecking_type = False
                        elif t == 'number':
                            tf.keyboard_type = ui.KEYBOARD_NUMBERS
                            tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
                            tf.autocorrection_type = False
                            tf.spellchecking_type = False
                        elif t == 'password':
                            tf.secure = True
                        
                        tf.clear_button_mode = 'while_editing'
                        tf.name = key
                        tf.delegate = self
                        cell.content_view.add_subview(tf)

                    elif t == 'check':
                        value = item.get('value', False)
                        group = item.get('group', None)
                        if value:
                            cell.accessory_type = 'checkmark'
                            cell.text_label.text_color = cell.tint_color
                        cell.text_label.text = title
                        if group:
                            if value:
                                self.values[group] = key
                        else:
                            self.values[key] = value
                    elif t == 'date' or t == 'datetime' or t == 'time':
                        value = item.get('value', datetime.datetime.now())
                        if type(value) == datetime.date:
                            value = datetime.datetime.combine(value, datetime.time())
                        if type(value) == datetime.time:
                            value = datetime.datetime.combine(value, datetime.date.today())
                        date_format = item.get('format', None)
                        if not date_format:
                            if t == 'date':
                                date_format = '%Y-%m-%d'
                            elif t == 'time':
                                date_format = '%H:%M'
                            else:
                                date_format = '%Y-%m-%d %H:%M'
                        item['format'] = date_format
                        cell.detail_text_label.text = value.strftime(date_format)
                        self.values[key] = value
                        cell.text_label.text = title
                    else:
                        cell.selectable = False
                        cell.text_label.text = item.get('title', '')

                    section_cells.append(cell)

        def addCell(self, item):
            cell = ui.TableViewCell('value1')
            cell.name = item.get('key', None) #добавляем имя для ячейки, для дальнейшей идентификации
            icon = item.get('icon', None)
            tint_color = item.get('tint_color', None)
            if tint_color:
                cell.tint_color = tint_color
            if icon:
                if isinstance(icon, str):
                    icon = ui.Image.named(icon)
                if tint_color:
                    cell.image_view.image = icon.with_rendering_mode(ui.RENDERING_MODE_TEMPLATE)
                else:
                    cell.image_view.image = icon
                
            title_color = item.get('title_color', None)
            if title_color:
                cell.text_label.text_color = title_color
            
            t = item.get('type', None)
            key = item.get('key', item.get('title', None))
            item['key'] = key
            title = item.get('title', '')
            value = item.get('value', '')
            self.values[key] = value
            placeholder = item.get('placeholder', '')
            cell.selectable = False
            cell.text_label.text = title
            label_width = ui.measure_string(title, font=cell.text_label.font)[0]
            if cell.image_view.image:
                label_width += min(64, cell.image_view.image.size[0] + 16)
            cell_width, cell_height = cell.content_view.width, cell.content_view.height
            tf = ui.TextField()
            tf_width = max(40, cell_width - label_width - 32)
            tf.frame = (cell_width - tf_width - 8, 1, tf_width, cell_height-2)
            tf.bordered = False
            tf.placeholder = placeholder
            tf.flex = 'W'
            tf.text = value
            tf.text_color = '#337097'
            if t == 'text':
                tf.autocorrection_type = item.get('autocorrection', None)
                tf.autocapitalization_type = item.get('autocapitalization', ui.AUTOCAPITALIZE_SENTENCES)
                tf.spellchecking_type = item.get('spellchecking', None)
            if t == 'url':
                tf.keyboard_type = ui.KEYBOARD_URL
                tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
                tf.autocorrection_type = False
                tf.spellchecking_type = False
            elif t == 'email':
                tf.keyboard_type = ui.KEYBOARD_EMAIL
                tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
                tf.autocorrection_type = False
                tf.spellchecking_type = False
            elif t == 'number':
                tf.keyboard_type = ui.KEYBOARD_NUMBERS
                tf.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
                tf.autocorrection_type = False
                tf.spellchecking_type = False
            elif t == 'password':
                tf.secure = True
            
            tf.clear_button_mode = 'while_editing'
            tf.name = key
            tf.delegate = self
            cell.content_view.add_subview(tf)

            self.cells[3].append(cell) #3 - Categories section

        def update_kb_height(self, h):
            self.view.content_inset = (0, 0, h, 0)
            self.view.scroll_indicator_insets = (0, 0, h, 0)
        
        def tableview_number_of_sections(self, tv):
            return len(self.cells)
        
        def tableview_title_for_header(self, tv, section):
            return self.sections[section][0]

        def tableview_title_for_footer(self, tv, section):
            s = self.sections[section]
            if len(s) > 2:
                return s[2]
            return None
        
        def tableview_number_of_rows(self, tv, section):
            return len(self.cells[section])
        
        def tableview_did_select(self, tv, section, row):
            sel_item = self.sections[section][1][row]
            t = sel_item.get('type', None)
            if t == 'check':
                key = sel_item['key']
                tv.selected_row = -1
                group = sel_item.get('group', None)
                cell = self.cells[section][row]
                if group:
                    for i, s in enumerate(self.sections):
                        for j, item in enumerate(s[1]):
                            if item.get('type', None) == 'check' and item.get('group', None) == group and item is not sel_item:
                                self.cells[i][j].accessory_type = 'none'
                                self.cells[i][j].text_label.text_color = None
                    cell.accessory_type = 'checkmark'
                    cell.text_label.text_color = cell.tint_color
                    self.values[group] = key
                else:
                    if cell.accessory_type == 'checkmark':
                        cell.accessory_type = 'none'
                        cell.text_label.text_color = None
                        self.values[key] = False
                    else:
                        cell.accessory_type = 'checkmark'
                        self.values[key] = True
            elif t == 'date' or t == 'time' or t == 'datetime':
                tv.selected_row = -1
                self.selected_date_key = sel_item['key']
                self.selected_date_value = self.values.get(self.selected_date_key)
                self.selected_date_cell = self.cells[section][row]
                self.selected_date_format = sel_item['format']
                self.selected_date_type = t
                if t == 'date':
                    mode = ui.DATE_PICKER_MODE_DATE
                elif t == 'time':
                    mode = ui.DATE_PICKER_MODE_TIME
                else:
                    mode = ui.DATE_PICKER_MODE_DATE_AND_TIME
                self.show_datepicker(mode)

        def tableview_can_delete(self, tv, section, row):
            if self.sections[section][0] == 'Categories:':
                return True
            else:
                return False

        def tableview_can_move(self, tv, section, row):
            if self.sections[section][0] == 'Categories:':
                return True
            else:
                return False

        def tableview_move_row(self, tv, from_section, from_row, to_section, to_row):
            if self.sections[from_section][0] == 'Categories:' and self.sections[to_section][0] == 'Categories:':
                if from_row == to_row:
                    return
                moved_item = self.cells[from_section][from_row]
                del self.cells[from_section][from_row]
                self.cells[from_section][to_row:to_row] = [moved_item]
                newCategories = []
                for i in self.cells[from_section]:
                    newCategories.append(i.text_label.text)
                self.values['newCategories'] = newCategories
            else:
                self.container_view.close()
                    
        def tableview_delete(self, tv, section, row):
            del self.cells[section][row]
            tv.delete_rows([(row, section), ])
            newCategories = []
            for i in self.cells[section]:
                newCategories.append(i.text_label.text)
            self.values['newCategories'] = newCategories
            
        def show_datepicker(self, mode):
            ui.end_editing()
            self.shield_view = ui.View()
            self.shield_view.flex = 'WH'
            self.shield_view.frame = (0, 0, self.view.width, self.view.height)
            
            self.dismiss_datepicker_button = ui.Button()
            self.dismiss_datepicker_button.flex = 'WH'
            self.dismiss_datepicker_button.frame = (0, 0, self.view.width, self.view.height)
            self.dismiss_datepicker_button.background_color = (0, 0, 0, 0.5)
            self.dismiss_datepicker_button.action = self.dismiss_datepicker
            self.dismiss_datepicker_button.alpha = 0.0
            self.shield_view.add_subview(self.dismiss_datepicker_button)

            self.date_picker = ui.DatePicker()
            self.date_picker.date = self.selected_date_value
            self.date_picker.background_color = 'white'
            self.date_picker.mode = mode
            self.date_picker.frame = (0, self.shield_view.height - self.date_picker.height, self.shield_view.width, self.date_picker.height)
            self.date_picker.flex = 'TW'
            self.date_picker.transform = ui.Transform.translation(0, self.date_picker.height)
            self.shield_view.add_subview(self.date_picker)

            self.container_view.add_subview(self.shield_view)
            
            def fade_in():
                self.dismiss_datepicker_button.alpha = 1.0
                self.date_picker.transform = ui.Transform.translation(0, 0)
            ui.animate(fade_in, 0.3)

        def dismiss_datepicker(self, sender):
            value = self.date_picker.date
            
            if self.selected_date_type == 'date':
                self.selected_date_cell.detail_text_label.text = value.strftime(self.selected_date_format)
            elif self.selected_date_type == 'time':
                self.selected_date_cell.detail_text_label.text = value.strftime(self.selected_date_format)
            else:
                self.selected_date_cell.detail_text_label.text = value.strftime(self.selected_date_format)

            self.values[self.selected_date_key] = value
            
            def fade_out():
                self.dismiss_datepicker_button.alpha = 0.0
                self.date_picker.transform = ui.Transform.translation(0, self.date_picker.height)
            def remove():
                self.container_view.remove_subview(self.shield_view)
                self.shield_view = None
            ui.animate(fade_out, 0.3, completion=remove)
        
        def tableview_cell_for_row(self, tv, section, row):
            return self.cells[section][row]
        
        def textfield_did_change(self, tf):
            self.values[tf.name] = tf.text

        def textfield_did_end_editing(self, tf):
            pass

        def textfield_should_return(self, tf):
            tf.end_editing()
            if tf.name == 'newCategory' and tf.text != '':
                a = {'title':tf.text, 'group':'categories'}
                self.addCell(a)
                self.view.reload()
                newCategories = []
                for i in self.cells[3]:
                    newCategories.append(i.text_label.text)
                self.values['newCategories'] = newCategories
                
        def switch_action(self, sender):
            self.values[sender.name] = sender.value
        
        def done_action(self, sender):
            if self.shield_view:
                self.dismiss_datepicker(None)
            else:
                ui.end_editing()
                self.was_canceled = False
                self.container_view.close()

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
        def will_close(self):
            pass

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

        cur.execute('''CREATE TABLE IF NOT EXISTS settings(
                            id INTEGER PRIMARY KEY,
                            categories TEXT,
                            initialMode TEXT,
                            currencySymbol TEXT,
                            localDateFormat TEXT)''')

        cur.execute('''INSERT INTO settings (id,
                        categories,
                        initialMode,
                        currencySymbol,
                        localDateFormat) VALUES(?, ?, ?, ?, ?)''', (DEFAULTSETTINGSID,
                            DEFAULTCATEGORIES,
                            INITIALMODE,
                            CURRENCYSYMBOL,
                            'Europe'))

        cur.execute('''INSERT INTO settings (id,
                        categories,
                        initialMode,
                        currencySymbol,
                        localDateFormat) VALUES(?, ?, ?, ?, ?)''', (USERSETTINGSID,
                            DEFAULTCATEGORIES,
                            INITIALMODE,
                            CURRENCYSYMBOL,
                            'Europe'))
        
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

    def addCategory(self, newCategory):
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        categories = db.execute('SELECT categories FROM settings WHERE id=?', (USERSETTINGSID, )).fetchone()[0]
        newCategories = categories+'\t'+newCategory
        db.execute('UPDATE settings SET categories=? WHERE id=?', (newCategories, USERSETTINGSID))
        connection.commit()
        connection.close()

    def getSettings(self, mode='user'):
        if mode == 'user': #user settings
            settingsId = 1
        elif mode == 'default': #default settings
            settingsId = 0
        else:
            raise ValueError('Несоответствующее значение')

        connection = sqlite3.connect(DB)
        connection.row_factory = sqlite3.Row
        db = connection.cursor()
        settings = db.execute('''SELECT categories as categories,
            initialMode as initialMode,
            currencySymbol as currencySymbol,
            localDateFormat as localDateFormat FROM settings WHERE id =?''', (settingsId, )).fetchone()
        connection.close()
        return settings

    def resetToDefaultSettings(self):
        a = self.getSettings(mode='default')
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        db.execute('''UPDATE settings SET initialMode=?,
            currencySymbol=?,
            localDateFormat=? WHERE id=?''', (a['initialMode'],
                a['currencySymbol'],
                a['localDateFormat'],
                USERSETTINGSID))
        connection.commit()
        connection.close()

    def updateSettings(self, settings):
        connection = sqlite3.connect(DB)
        db = connection.cursor()
        db.execute('''UPDATE settings SET categories=?,
            initialMode=?,
            currencySymbol=?,
            localDateFormat=? WHERE id=?''', (settings['newCategories'],
                settings['initialMode'],
                settings['currencySymbol'],
                settings['localDateFormat'],
                USERSETTINGSID))
        connection.commit()
        connection.close()

class Controller():
    def __init__(self):
        self.model = Model(self)
        self.gui = GUI(self)
        self.settings = self.getSettings() #словарь с настройками

        self.date = self.getNow() #datetime object
        self.fromDate = None #datetime object
        self.toDate = None #datetime object
        
        self.gui.update(self.getNameForMainTable(), self.getItemsForMainTable())

    def periodButtonAction(self, result):
        self.settings['mode'] = result['mode']
        self.fromDate = result.get('fromDate', None)
        self.toDate = result.get('toDate', None)
        self.gui.update(self.getNameForMainTable(), self.getItemsForMainTable())     

    def calendarButtonAction(self, result):
        self.date = result
        self.gui.update(self.getNameForMainTable(), self.getItemsForMainTable())

    def settingsButtonAction(self, settings):
        if settings['reset'] == True:
            self.model.resetToDefaultSettings()
            self.updateSettings()
            self.gui.update(self.getNameForMainTable(), self.getItemsForMainTable())
        else:
            self.settings['initialMode'] = settings['initialMode']
            self.settings['localDateFormat'] = settings['localDateFormat']
            self.settings['currencySymbol'] = settings['currencySymbol']
            if settings.get('newCategories', None):
                self.settings['newCategories'] = '\t'.join(settings['newCategories'])
            else:
                self.settings['newCategories'] = '\t'.join(self.settings['categories'])
            self.model.updateSettings(self.settings)
            self.updateSettings()
            self.gui.update(self.getNameForMainTable(), self.getItemsForMainTable())

    def searchButtonAction(self):
        pass

    def addButtonAction(self, transaction, transactionId=None):
        if transaction['newCategory'] != '': #у нас есть новая категория
            self.model.addCategory(transaction['newCategory'])
            transaction['category'] = transaction['newCategory']
            self.updateSettings()

        transaction['date'] = transaction['date'].strftime('%Y-%m-%d %H:%M:%S')
        if transactionId and transaction['category'] and transaction['price']: #режим редактирования транзакции, т. к. есть id, будем ее перезаписывать по этому id
            transaction['id'] = transactionId
            self.model.updateTransaction(transaction)
        elif transaction['category'] != '' and transaction['price'] != '': #режим добавления транзакции, т. к. нет id
            self.model.addTransaction(transaction)
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

    def floatToPrice(self, fPrice, mode='rough'):
        if fPrice == None:
            return '0 ₽'
        elif mode == 'rough':
            return (format(fPrice, ',.0f').replace(',', '  ')+ ' '+self.settings['currencySymbol'])
        elif mode == 'precisely':
            return (format(fPrice, ',.2f').replace(',', '  ')+' '+self.settings['currencySymbol'])
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

    def getNameForMainTable(self):
        if self.settings['mode'] == 'Day':
            period = (self.date.strftime('%Y-%m-%d'), self.date.strftime('%Y-%m-%d'))
            total = self.model.getTotalPriceFromPeriod(period)
            return (self.date.strftime(LOCALDATEFORMAT[self.settings['localDateFormat']]['day'])+' ('+self.floatToPrice(total)+')')
        elif self.settings['mode'] == 'Month':
            period = ((self.date.strftime('%Y-%m')+'-01'), (self.date.strftime('%Y-%m')+'-31'))
            total = self.model.getTotalPriceFromPeriod(period)
            return (self.date.strftime(LOCALDATEFORMAT[self.settings['localDateFormat']]['month'])+' ('+self.floatToPrice(total)+')')
        elif self.settings['mode'] == 'Year':
            period = ((self.date.strftime('%Y')+'-01-01'), (self.date.strftime('%Y')+'-12-31'))
            total = self.model.getTotalPriceFromPeriod(period)
            return (self.date.strftime(LOCALDATEFORMAT[self.settings['localDateFormat']]['year'])+' ('+self.floatToPrice(total)+')')
        elif self.settings['mode'] == 'Custom period':
            period = (self.fromDate.strftime('%Y-%m-%d'), self.toDate.strftime('%Y-%m-%d'))
            total = self.model.getTotalPriceFromPeriod(period)
            return (self.fromDate.strftime(LOCALDATEFORMAT[self.settings['localDateFormat']]['short'])+' - '+self.toDate.strftime(LOCALDATEFORMAT[self.settings['localDateFormat']]['short'])+' ('+self.floatToPrice(total)+')')
        elif self.settings['mode'] == 'All time':
            total = self.model.getTotalPriceFromAllTime()
            return ('All'+' ('+self.floatToPrice(total)+')')
        else:
            raise ValueError('Несоответствующее значение')

    def getItemsForMainTable(self):
        if self.settings['mode'] == 'Day':
            period = (self.date.strftime('%Y-%m-%d'), self.date.strftime('%Y-%m-%d'))
            getTransaction = self.model.getTransactionsFromPeriod
        elif self.settings['mode'] == 'Month':
            period = ((self.date.strftime('%Y-%m')+'-01'), (self.date.strftime('%Y-%m')+'-31'))
            getTransaction = self.model.getTransactionsFromPeriod
        elif self.settings['mode'] == 'Year':
            period = ((self.date.strftime('%Y')+'-01-01'), (self.date.strftime('%Y')+'-12-31'))
            getTransaction = self.model.getTransactionsFromPeriod
        elif self.settings['mode'] == 'Custom period':
            period = (self.fromDate.strftime('%Y-%m-%d'), self.toDate.strftime('%Y-%m-%d'))
            getTransaction = self.model.getTransactionsFromPeriod
        elif self.settings['mode'] == 'All time':
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
                    'rowDate':datetime.datetime.strptime(row['dates'].split('\t')[i], DEFAULTFORMATDAY).strftime(LOCALDATEFORMAT[self.settings['localDateFormat']]['day']), #меняем дату под локаль
                    'rowName':row['names'].split('\t')[i],
                    'rowSum':self.floatToPrice(float(row['prices'].split('\t')[i]))}
                string['rows'].append(r)
            result.append(string)
        return result

    def getTransaction(self, rowId):
        rawData = self.model.getTransaction(rowId)
        transactionData = {'id':rawData[0], 'name':rawData[1], 'category':rawData[2], 'price':rawData[3], 'date':rawData[4], 'note':rawData[5]}
        return transactionData

    def addFastTransaction(self):
        #adding transaction from iOS shortcuts
        self.gui.addButtonAction(None)

    def getSettings(self, mode='user'):
        a = self.model.getSettings(mode)
        settings = {}
        
        settings['categories'] = a['categories'].split('\t')
        settings['mode'] = a['initialMode']
        settings['initialMode'] = a['initialMode']
        settings['currencySymbol'] = a['currencySymbol']
        settings['localDateFormat'] = a['localDateFormat']
        
        return settings

    def updateSettings(self):
        self.settings = self.getSettings()

controller = Controller()
if len(sys.argv) > 1:
    if sys.argv[1] == 'addTransaction':
        controller.addFastTransaction()
    elif sys.argv[1] == 'start':
        pass #обычный запуск без доп действий
