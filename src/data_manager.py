import json
import os


class DataManager:
    """Handles loading and saving all application data from/to JSON files."""

    def __init__(self, data_dir="."):
        self.data_dir = data_dir
        self.data_keys = ["users", "bakers", "picks", "results", "final_scores"]
        self.data = self._load_all_data()

    def _load_all_data(self):
        """Loads all data files on initialization."""
        loaded_data = {key: {} for key in self.data_keys}
        loaded_data["bakers"] = []  # Bakers should be a list

        for key in self.data_keys:
            filename = os.path.join(self.data_dir, f"{key}.json")
            if os.path.exists(filename):
                try:
                    with open(filename, "r") as f:
                        content = f.read()
                        if content:
                            loaded_data[key] = json.loads(content)
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
        return loaded_data

    def save_data(self, data_type):
        """Saves a specific type of data to its corresponding JSON file."""
        if data_type in self.data_keys:
            filename = os.path.join(self.data_dir, f"{data_type}.json")
            with open(filename, "w") as f:
                json.dump(self.data[data_type], f, indent=2, default=str)
        else:
            raise ValueError(f"Unknown data type: {data_type}")

    def get_data(self):
        """Returns the entire data dictionary."""
        return self.data

    def reset_all_data(self):
        """Deletes all data files and reloads the state."""
        for key in self.data_keys:
            filename = os.path.join(self.data_dir, f"{key}.json")
            if os.path.exists(filename):
                os.remove(filename)
        # Reload the data to reset the state
        self.data = self._load_all_data()
