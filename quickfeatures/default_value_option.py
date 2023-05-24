class DefaultValueOption():

    def __init__(self, name: str, data_type: str):
        self.value = None
        self.selected = False
        self.valid = True
        self.name = name
        self.type = data_type

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def get_name(self) -> str:
        return self.name

    def get_type(self) -> str:
        return self.type

    def is_valid(self) -> bool:
        return self.valid

    def is_selected(self) -> bool:
        return self.selected

    def toggle_selected(self):
        self.set_selected(not self.is_selected())

    def set_selected(self, value) -> None:

        if value:
            if not self.is_selected() and self.is_valid():
                self.selected = True
        else:
            if self.is_selected():
                self.selected = False