import math
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QPushButton, QGridLayout
from PySide6.QtCore import Slot
from variables import MEDIUM_FONT_SIZE
from utils import isNumOrDot, isEmpty, isValidNumber, convertoNumber


if TYPE_CHECKING:
    from display import Display
    from main_window import MainWindow
    from info import Info

class Button(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configStyle()

    def configStyle(self):
        font = self.font()
        font.setPixelSize(MEDIUM_FONT_SIZE)
        self.setFont(font)
        self.setMinimumSize(75, 75)
        
        

class ButtonsGrid(QGridLayout):
    def __init__(self, display: 'Display', info: 'Info', window: 'MainWindow',
                  *args, **kwargs
                 ) -> None:
        super().__init__(*args, **kwargs)

        self._gridMask = [
             ['C', 'D', '^', '/'],
             ['7', '8', '9', '*'],
             ['4', '5', '6', '-'],
             ['1', '2', '3', '+'],
             ['N',  '0', '.', '='],
         ]
        self.display = display
        self.info = info
        self.window = window
        self._equation = ''
        self._equationInitialValue = 'Sua conta'
        self._left = None
        self._right = None
        self._op = None

        self.equation = self._equationInitialValue
        self._makeGrid()

    @property
    def equation (self):
        return self._equation
    
    @equation.setter
    def equation(self, value):
        self._equation = value
        self.info.setText(value)


    def _makeGrid(self):
        self.display.eqPressed.connect(self._eq)
        self.display.delPressed.connect(self._bakespace)
        self.display.clearPressed.connect(self._clear)
        self.display.inputPressed.connect(self._inserToDisplay)
        self.display.operatorPressed.connect(self._configLeftOp)

        for rowNumber, rowDate in enumerate(self._gridMask):
            for columnNumber, buttonText in enumerate(rowDate):
                button = Button(buttonText)

                if not isNumOrDot(buttonText) and not isEmpty(buttonText):
                    button.setProperty('cssClass', 'specialButton')
                    self._configSpecialButton(button)

                self.addWidget(button, rowNumber, columnNumber)
                slot = self._makeSlot(self._inserToDisplay, buttonText)
                self._connectButtonClicked(button, slot)
    
    def _connectButtonClicked(self, button, slot):
        button.clicked.connect(slot)

    def _configSpecialButton(self, button):
        text = button.text()
        
        if text == 'C':
            self._connectButtonClicked(button, self._clear)
        
        if text == 'D':
            self._connectButtonClicked(button, self._bakespace)
        
        if text == 'N':
            self._connectButtonClicked(button, self._invertNumber)
        
        if text in '+-/*^':
            self._connectButtonClicked(
                 button,
                self._makeSlot(self._configLeftOp, text)
            )
        
        if text == '=':
            self._connectButtonClicked(button, self._eq)

    @Slot()
    def _makeSlot(self, func, *args, **kwargs):
        @Slot(bool)
        def realSlot(_):
            func( *args, **kwargs)
        return realSlot

    @Slot()
    def _invertNumber(self):
        displayText = self.display.text()
        
        if not isValidNumber(displayText):
            return
        
        number = convertoNumber(displayText) * -1

        self.display.setText(str(number))


    @Slot()
    def _inserToDisplay(self, text):
        newDisplayValue = self.display.text() + text

        if not isValidNumber(newDisplayValue):
            return

        self.display.insert(text)
        self.display.setFocus()
        
    @Slot()
    def _clear(self):
        self._left = None
        self._right = None
        self._op = None

        self.equation = self._equationInitialValue
        self.display.clear()
        self.display.setFocus()

    @Slot()
    def _configLeftOp(self, text):
        displayText = self.display.text()
        self.display.clear()
        self.display.setFocus()
        
        # Se a pessoa clicou no operador sem
        # configurar qualquer número
        if not isValidNumber(displayText) and self._left is None:
            self._showError('Você não digitou nada.')
            return
        
        # Se houver algo no número da esquerda,
        # não fazemos nada. aguardaremos o número da direita.
        if self._left is None:
            self._left = convertoNumber(displayText)

        self._op = text
        self.equation = f'{self._left} {self._op} ??'

    @Slot()
    def _eq(self):
        displayText = self.display.text()

        if not isValidNumber(displayText) or self._left is None:
            self._showError('Conta incompleta.')
            return
        
        self._right = convertoNumber(displayText)
        self.equation = f'{self._left} {self._op} {self._right}'
        result = 'error'

        try:
            if '^' in self.equation and isinstance(self._left, int | float):
                result = math.pow(self._left, self._right)
                #result = eval(self.equation.replace('^', '**')) #poderia ter feito isso, mas optei por importar o math
            else:
                result = eval(self.equation)
        except ZeroDivisionError:
            self._showError('Divisão por zero.')
        except OverflowError:
            self._showError('Essa conta não pode ser realizada.')

        self.display.clear()
        self.info.setText(f'{self.equation} = {result}')
        self._left = result
        self._right = None
        self.display.setFocus()

        if result == 'error':
            self._left = None
    
    @Slot()
    def _bakespace(self):
        self.display.backspace()
        self.display.setFocus()

    def _makeDialog(self, text):
        msgBox = self.window.makeMsgBox()
        msgBox.setText(text)
        return msgBox

    def _showError(self, text):
        msgBox = self._makeDialog(text)
        msgBox.setText(text)
        msgBox.setIcon(msgBox.Icon.Critical)
        msgBox.exec()
        self.display.setFocus()
    

    def _showInfo(self, text):
        msgBox = self._makeDialog(text)
        msgBox.setText(text)
        msgBox.setIcon(msgBox.Icon.Information)
        msgBox.exec()
        self.display.setFocus()