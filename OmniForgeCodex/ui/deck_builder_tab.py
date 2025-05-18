from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget

class DeckBuilderTab(QWidget):
    def __init__(self, deck_builder, output_generator):
        super().__init__()
        self.deck_builder = deck_builder
        self.output_generator = output_generator
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Search section
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for cards...")
        search_button = QPushButton("Search")
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # Results section
        self.results_list = QListWidget()
        layout.addWidget(QLabel("Search Results"))
        layout.addWidget(self.results_list)

        # Deck section
        self.deck_list = QListWidget()
        layout.addWidget(QLabel("Current Deck"))
        layout.addWidget(self.deck_list)

        # Control buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add to Deck")
        remove_button = QPushButton("Remove from Deck")
        save_button = QPushButton("Save Deck")
        button_layout.addWidget(add_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)

        self.setLayout(layout) 