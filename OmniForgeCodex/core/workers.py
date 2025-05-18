from PySide6.QtCore import QThread, Signal

class InventoryLoadWorker(QThread):
    progress = Signal(str)
    finished = Signal()

    def __init__(self, inventory_manager, file_path):
        super().__init__()
        self.inventory_manager = inventory_manager
        self.file_path = file_path

    def run(self):
        self.inventory_manager.load_csv_inventory(self.file_path)
        self.finished.emit()

class DeckBuildWorker(QThread):
    progress = Signal(str)
    finished = Signal(list)

    def __init__(self, deck_builder, prefs, num_decks, strategy):
        super().__init__()
        self.deck_builder = deck_builder
        self.prefs = prefs
        self.num_decks = num_decks
        self.strategy = strategy

    def run(self):
        decks = self.deck_builder.build_decks_iterative(self.prefs, self.num_decks, self.strategy)
        self.finished.emit(decks)

class ForgeSimWorker(QThread):
    progress = Signal(str)
    finished = Signal(list)

    def __init__(self, simulator, deck_path, opp_paths, format_, runs):
        super().__init__()
        self.simulator = simulator
        self.deck_path = deck_path
        self.opp_paths = opp_paths
        self.format_ = format_
        self.runs = runs

    def run(self):
        results = self.simulator.run_batch_simulations(self.deck_path, self.opp_paths, self.format_, self.runs)
        self.finished.emit(results)
