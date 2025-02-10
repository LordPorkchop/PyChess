import os
import stockfish
import tkinter as tk
from itertools import product
from PIL import Image, ImageTk


stockfish_path = os.path.join(os.path.dirname(
    __file__), "stockfish", "stockfish.exe")
assets_dir = os.path.join(os.path.dirname(__file__), "assets")
save_dir = os.path.join(os.path.dirname(__file__), "games")
icon_path = os.path.join(assets_dir, "icon.ico")


class UnknownPieceError(Exception):
    def __init__(self, msg: str, **kwargs):
        super.__init__(message=msg, **kwargs)


class UnknownCoordinatesError(Exception):
    def __init__(self, msg: str, **kwargs):
        super.__init__(message=msg, **kwargs)


class ChessEngine(stockfish.Stockfish):
    def __init__(self):
        super.__init__(path=stockfish_path)


class ChessBoard:
    def __init__(
        self,
        root: tk.Tk,
        asset_location: os.PathLike,
        tile_size: int = 60,
        start_flipped: bool = False,
        white_color_code: str = "#ffcf9f",
        black_color_code: str = "#d28c45",
        select_color_code: str = "#cad549",
        mark_color_code: str = "#ff3232"
    ):
        self.root = root

        self.assets_path = asset_location

        self.canvas = tk.Canvas(root, width=8*tile_size, height=8*tile_size)
        self.canvas.pack(side="left")

        self.tile_size = tile_size

        self._white = white_color_code
        self._black = black_color_code
        self._colors = (self._white, self._black)

        self._select = select_color_code
        self._mark = mark_color_code

        self.selected_cell = None
        self.marked_cells = []

        self._flipped = False

        self.board = [
            ["BR", "BN", "BB", "BQ", "BK", "BB", "BN", "BR"],
            ["BP", "BP", "BP", "BP", "BP", "BP", "BP", "BP"],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["WP", "WP", "WP", "WP", "WP", "WP", "WP", "WP"],
            ["WR", "WN", "WB", "WQ", "WK", "WB", "WN", "WR"]
        ]

        self.board_rects = {}

        self.__moves = []

        self.turn = "White"

        self._piece_names = ["r", "n", "b", "q", "k", "b", "n", "r"]

        self.rows = ["8", "7", "6", "5", "4", "3", "2", "1"]
        self.cols = ["A", "B", "C", "D", "E", "F", "G", "H"]

        self.coords = ["".join(x) for x in product(self.cols, self.rows)]

        self.__piece_images = self.__fetch_assets()

        self.__board_is_shown = True

        if start_flipped:
            self.flip()

    def __fetch_assets(self) -> dict:
        piece_files = {}
        pieces = ["wk", "wq", "wr", "wn", "wb",
                  "wp", "bk", "bq", "br", "bn", "bb", "bp"]

        for path, _, files in os.walk(self.assets_path):
            for file in files:
                filename = file.split(".")[0]
                if filename.lower() in pieces:
                    piece_files.update(
                        {filename.lower(): os.path.join(path, file)})
        piece_images = {}

        for name, path in piece_files.items():
            img = Image.open(path)
            img_rszd = img.resize(
                (self.tile_size, self.tile_size), Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img_rszd)
            piece_images.update({name.upper(): img_tk})

        self.root.piece_images = piece_images

        return piece_images

    def change_colors(self, new_white: str = "#ffcf9f", new_black: str = "#d28c45") -> bool:
        if new_white.startswith("#") and new_black.startswith("#") and new_white != new_black and len(new_white) == 7 and len(new_black) == 7:
            self._white = new_white
            self._black = new_black
            return True
        else:
            return False

    def flip(self, draw_immediate: bool = False):
        self._flipped = not self._flipped
        self.board.reverse()
        self.rows.reverse()
        self.cols.reverse()
        if draw_immediate:
            self.draw()

    def reset(self):
        if self._flipped:
            self.flip()
        self.board = [
            ["BR", "BN", "BB", "BQ", "BK", "BB", "BN", "BR"],
            ["BP", "BP", "BP", "BP", "BP", "BP", "BP", "BP"],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["  ", "  ", "  ", "  ", "  ", "  ", "  ", "  "],
            ["WP", "WP", "WP", "WP", "WP", "WP", "WP", "WP"],
            ["WR", "WN", "WB", "WQ", "WK", "WB", "WN", "WR"]
        ]
        self.__moves = []

        self.canvas.delete("all")

        for row in range(8):
            for col in range(8):
                color = self._colors[(row + col) % 2]
                x1, y1 = col * self.tile_size, row * self.tile_size
                x2, y2 = x1 + self.tile_size, y1 + self.tile_size
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="")
                self.board_rects[f"{row},{col}"] = rect

                text_color = self._white if color == self._black else self._black

                if row == 7:
                    self.canvas.create_text(x1 + self.tile_size - 1, y1 + self.tile_size - 1, text=chr(
                        97 + col).upper(), anchor="se", font=("Arial", 8, "bold"), fill=text_color)
                if col == 0:
                    self.canvas.create_text(
                        x1 + 3, y1 + 3, text=str(8 - row), anchor="nw", font=("Arial", 8, "bold"), fill=text_color)

        for row, line in enumerate(self.board):
            for col, cell in enumerate(line):
                if cell != "  ":
                    self.canvas.create_image(
                        30 + col * self.tile_size, 30 + row * self.tile_size, image=self.__piece_images[cell], tags="piece")

    def update(self):
        self.canvas.delete("piece")
        for row, line in enumerate(self.board):
            for col, cell in enumerate(line):
                if cell != "  ":
                    self.canvas.create_image(
                        30 + col * self.tile_size, 30 + row * self.tile_size, image=self.__piece_images[cell], tags="piece")

    def draw(self):
        self.canvas.delete("all")

        for row in range(8):
            for col in range(8):
                color = self._colors[(row + col) % 2]
                x1, y1 = col * self.tile_size, row * self.tile_size
                x2, y2 = x1 + self.tile_size, y1 + self.tile_size
                rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline="")
                self.board_rects[f"{row},{col}"] = rect

                text_color = self._white if color == self._black else self._black

                if row == 7:
                    self.canvas.create_text(x1 + self.tile_size - 1, y1 + self.tile_size - 1, text=chr(
                        97 + col).upper(), anchor="se", font=("Arial", 8, "bold"), fill=text_color)
                if col == 0:
                    self.canvas.create_text(
                        x1 + 3, y1 + 3, text=str(8 - row), anchor="nw", font=("Arial", 8, "bold"), fill=text_color)

        for row, line in enumerate(self.board):
            for col, cell in enumerate(line):
                if cell != "  ":
                    piece_x = (0.5 * self.tile_size) + col * self.tile_size
                    piece_y = (0.5 * self.tile_size) + row * self.tile_size
                    self.canvas.create_image(
                        piece_x, piece_y, image=self.__piece_images[cell], tags="piece")

    def hide(self):
        if self.__board_is_shown:
            self.__board_is_shown = False
            self.canvas.pack_forget()

    def show(self):
        if not self.__board_is_shown:
            self.__board_is_shown = True
            self.canvas.pack()

    def get_moves(self) -> tuple:
        return tuple(self.__moves)

    def get_legal_moves(self, cell: str) -> list:
        if cell.upper() not in self.coords:
            raise UnknownCoordinatesError(
                f"{cell} is not a valid coordinate pair. Please use any from A1 to H8")

        moves = []

        row_idx = self.rows.index(cell[1].upper())
        col_idx = self.cols.index(cell[0].upper())
        row = cell[1]
        col = cell[0].lower()
        piece = self.board[row_idx][col_idx].lower()
        piece_color = piece[0].lower()
        piece_type = piece[1]
        print(piece, cell, str(col_idx) + str(row_idx), end=": ")

        match piece_type:
            case " ":
                return None
            case "p":
                if piece_color == "w":
                    if self.__is_empty(row_idx - 1, col_idx):
                        moves.append(
                            col + row + col + self.rows[row_idx - 1])

                        if row_idx == 6:
                            if self.__is_empty(row_idx - 2, col_idx):
                                moves.append(
                                    col + row + col + self.rows[row_idx - 2])

                    if col_idx > 0:
                        if not self.__is_empty(row_idx - 1, col_idx - 1) and self.__get_color(row_idx - 1, col_idx - 1) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx - 1] + row)

                    if col_idx < 7:
                        if not self.__is_empty(row_idx - 1, col_idx + 1) and self.__get_color(row_idx - 1, col_idx - 1) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx + 1] + self.rows[row_idx - 1])
                else:
                    if self.__is_empty(row_idx + 1, col_idx):
                        moves.append(
                            col + row + col + self.rows[row_idx + 1])

                        if row_idx == 1:
                            if self.__is_empty(row_idx + 2, col_idx):
                                moves.append(
                                    col + row + col + self.rows[row_idx + 2])

                    if col_idx > 0:
                        if not self.__is_empty(row_idx + 1, col_idx - 1) and self.__get_color(row_idx + 1, col_idx - 1) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx - 1] + self.rows[row_idx + 1])

                    if col_idx < 7:
                        if not self.__is_empty(row_idx + 1, col_idx + 1) and self.__get_color(row_idx + 1, col_idx - 1) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx + 1] + self.rows[row_idx + 1])

            case "r":
                for m in range(8):
                    try:
                        if self.__is_empty(row_idx + m, col_idx):
                            moves.append(col + row + col +
                                         self.rows[row_idx + m])
                        elif self.__get_color(row_idx + m, col_idx) != piece_color:
                            moves.append(moves.append(
                                col + row + col + self.rows[row_idx + m]))
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx - m, col_idx):
                            moves.append(col + row + col +
                                         self.rows[row_idx - m])
                        elif self.__get_color(row_idx - m, col_idx) != piece_color:
                            moves.append(moves.append(
                                col + row + col + self.rows[row_idx - m]))
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx, col_idx + m):
                            moves.append(
                                col + row + self.cols[col_idx + m] + row)
                        elif self.__get_color(row_idx, col_idx + m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx + m] + row)
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx, col_idx - m):
                            moves.append(
                                col + row + self.cols[col_idx - m] + row)
                        elif self.__get_color(row_idx, col_idx - m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx - m] + row)
                            break
                    except IndexError:
                        break

            case "b":
                for m in range(8):
                    try:
                        if self.__is_empty(row_idx + m, col_idx + m):
                            moves.append(
                                col + row + self.cols[col_idx + m] + self.rows[row_idx + m])
                        elif self.__get_color(row_idx + m, col_idx + m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx + m] + self.rows[row_idx + m])
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx - m, col_idx + m):
                            moves.append(
                                col + row + self.cols[col_idx + m] + self.rows[row_idx - m])
                        elif self.__get_color(row_idx - m, col_idx + m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx + m] + self.rows[row_idx - m])
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx + m, col_idx - m):
                            moves.append(
                                col + row + self.cols[col_idx - m] + self.rows[row_idx + m])
                        elif self.__get_color(row_idx + m, col_idx - m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx - m] + self.rows[row_idx + m])
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx - m, col_idx - m):
                            moves.append(
                                col + row + self.cols[col_idx - m] + self.rows[row_idx - m])
                        elif self.__get_color(row_idx - m, col_idx - m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx - m] + self.rows[row_idx - m])
                            break
                    except IndexError:
                        break

            case "q":
                for m in range(8):
                    try:
                        if self.__is_empty(row_idx + m, col_idx + m):
                            moves.append(
                                col + row + self.cols[col_idx + m] + self.rows[row_idx + m])
                        elif self.__get_color(row_idx + m, col_idx + m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx + m] + self.rows[row_idx + m])
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx - m, col_idx + m):
                            moves.append(
                                col + row + self.cols[col_idx + m] + self.rows[row_idx - m])
                        elif self.__get_color(row_idx - m, col_idx + m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx + m] + self.rows[row_idx - m])
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx + m, col_idx - m):
                            moves.append(
                                col + row + self.cols[col_idx - m] + self.rows[row_idx + m])
                        elif self.__get_color(row_idx + m, col_idx - m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx - m] + self.rows[row_idx + m])
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx - m, col_idx - m):
                            moves.append(
                                col + row + self.cols[col_idx - m] + self.rows[row_idx - m])
                        elif self.__get_color(row_idx - m, col_idx - m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx - m] + self.rows[row_idx - m])
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx + m, col_idx):
                            moves.append(col + row + col +
                                         self.rows[row_idx + m])
                        elif self.__get_color(row_idx + m, col_idx) != piece_color:
                            moves.append(moves.append(
                                col + row + col + self.rows[row_idx + m]))
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx - m, col_idx):
                            moves.append(col + row + col +
                                         self.rows[row_idx - m])
                        elif self.__get_color(row_idx - m, col_idx) != piece_color:
                            moves.append(moves.append(
                                col + row + col + self.rows[row_idx - m]))
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx, col_idx + m):
                            moves.append(
                                col + row + self.cols[col_idx + m] + row)
                        elif self.__get_color(row_idx, col_idx + m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx + m] + row)
                            break
                    except IndexError:
                        break

                for m in range(8):
                    try:
                        if self.__is_empty(row_idx, col_idx - m):
                            moves.append(
                                col + row + self.cols[col_idx - m] + row)
                        elif self.__get_color(row_idx, col_idx - m) != piece_color:
                            moves.append(
                                col + row + self.cols[col_idx - m] + row)
                            break
                    except IndexError:
                        break

            case "k":
                try:
                    if self.__is_empty(row_idx + 1, col_idx) or self.__get_color(row_idx + 1, col_idx):
                        moves.append(col + row + col + self.rows[row_idx + 1])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx + 1, col_idx + 1) or self.__get_color(row_idx + 1, col_idx + 1):
                        moves.append(
                            col + row + self.cols[col_idx + 1] + self.rows[row_idx + 1])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx, col_idx + 1) or self.__get_color(row_idx, col_idx + 1):
                        moves.append(col + row + self.cols[col_idx + 1] + row)
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx - 1, col_idx + 1) or self.__get_color(row_idx - 1, col_idx + 1):
                        moves.append(
                            col + row + self.cols[col_idx + 1] + self.rows[row_idx - 1])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx - 1, col_idx) or self.__get_color(row_idx - 1, col_idx):
                        moves.append(col + row + col + self.rows[row_idx - 1])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx - 1, col_idx - 1) or self.__get_color(row_idx - 1, col_idx - 1):
                        moves.append(
                            col + row + self.cols[col_idx - 1] + self.rows[row_idx + 1])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx, col_idx - 1) or self.__get_color(row_idx, col_idx - 1):
                        moves.append(col + row + self.cols[col_idx - 1] + row)
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx + 1, col_idx - 1) or self.__get_color(row_idx + 1, col_idx - 1):
                        moves.append(
                            col + row + self.cols[col_idx - 1] + self.row[row_idx + 1])
                except IndexError:
                    pass

            case "n":
                try:
                    if self.__is_empty(row_idx - 2, col_idx + 1) or self.__get_color(row_idx - 2, col_idx + 1) != piece_color:
                        moves.append(
                            col + row + self.cols[col_idx + 1] + self.rows[row_idx - 2])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx - 1, col_idx + 2) or self.__get_color(row_idx - 1, col_idx + 2) != piece_color:
                        moves.append(
                            col + row + self.cols[col_idx + 2] + self.rows[row_idx - 1])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx + 1, col_idx + 2) or self.__get_color(row_idx + 1, col_idx + 2) != piece_color:
                        moves.append(
                            col + row + self.cols[col_idx + 2] + self.rows[row_idx + 1])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx + 2, col_idx + 1) or self.__get_color(row_idx + 2, col_idx + 1) != piece_color:
                        moves.append(
                            col + row + self.cols[col_idx + 1] + self.rows[row_idx + 2])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx + 2, col_idx - 1) or self.__get_color(row_idx + 2, col_idx - 1) != piece_color:
                        moves.append(
                            col + row + self.cols[col_idx - 1] + self.rows[row_idx + 2])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx + 1, col_idx - 2) or self.__get_color(row_idx + 1, col_idx - 2) != piece_color:
                        moves.append(
                            col + row + self.cols[col_idx - 2] + self.rows[row_idx + 1])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx - 1, col_idx - 2) or self.__get_color(row_idx - 1, col_idx - 2) != piece_color:
                        moves.append(
                            col + row + self.cols[col_idx - 2] + self.rows[row_idx - 1])
                except IndexError:
                    pass

                try:
                    if self.__is_empty(row_idx - 2, col_idx - 1) or self.__get_color(row_idx - 2, col_idx - 1) != piece_color:
                        moves.append(
                            col + row + self.cols[col_idx - 1] + self.rows[row_idx - 2])
                except IndexError:
                    pass

            case _:
                return None

        moves = [x.lower() for x in moves]
        return moves

    def __is_empty(self, row: int, col: int):
        if self.board[row][col] == "  ":
            return True
        else:
            return False

    def __get_color(self, row: int, col: int):
        if self.board[row][col].startswith("W"):
            return "w"
        elif self.board[row][col].startswith("B"):
            return "b"


def main():
    root = tk.Tk()
    root.title("PyChess")
    root.iconbitmap(icon_path)
    root.geometry("600x485")
    root.minsize(485, 485)

    board = ChessBoard(root, assets_dir)
    board.draw()

    root.mainloop()


if __name__ == "__main__":
    main()
