from helper import *


class TUI:
    def __init__(self):
        self.table = ''
        self.flash_message = ''
        self.main_view()

    def main_view(self):
        self.clear()
        print(TITLE)
        option = get_option(["Connect to Existing Sqlite DB File", "Create a new Database", "Exit"])
        commands = {'Connect to Existing Sqlite DB File': self.connect, 'Create a new Database': self.create,
                    'Exit': self.exit}
        commands[option]()

    def connect(self):
        self.clear()
        self.db_path = get_text_input(">>> Enter the Path of your Sqlite DB File").strip()
        while 1:
            if not self.db_path:
                self.main_view()
                return
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.c = self.conn.cursor()
                break
            except Exception as e:
                print("\n  Unable to connect to the specified DB File, with Error Message:\n", '  ', e)
            self.db_path = get_text_input(">>> Enter the Path of your Sqlite DB File again").strip()
        self.clear()
        print(
            f"  ==================================================\n  {Colors.GREEN}Successfully Connected To: {self.db_path}{Colors.ENDC}\n  ==================================================\n")
        while 1:
            cmd = get_option(
                ["Execute a new command", "View all records", "Disconnect Sqlite DB and Back to Main Page"])
            if cmd == 'Disconnect Sqlite DB and Back to Main Page':
                self.c.close()
                self.conn.close()
                self.flash("Disconnected Sqlite DB: " + self.db_path)
                self.main_view()
                return
            self.clear()
            if cmd == "Execute a new command":
                self.execute(get_text_input("Type the SQLite query below"))
            if cmd == "View all records":
                self.view_all_records()
            print('\n ', '-' * 48, end='\n')

    def create(self):
        self.clear()

    def exit(self):
        self.clear()
        print(BYE)
        exit()

    def flash(self, message):
        self.flash_message = message

    def clear(self):
        if os.name == 'posix':
            __ = os.system('clear')
        else:
            __ = os.system('cls')
        if self.flash_message:
            color_print(Colors.GREEN, " *** ", self.flash_message, ' ***')
            self.flash_message = ''

    def execute(self, command: str, wildcards: Iterable = ()):
        if not command or not command.strip():
            if isinstance(command, str):
                self.flash("You just entered an empty query")
            self.clear()
            return
        spinner = Spinner(start=False)
        try:
            print("\n  executing the command ", end='')
            self.c.execute(command, wildcards)
            spinner.start()
            self.clear()
            print("\n  You entered:")
            print(indent(command, 2), '\n')
            if 'select' in command.lower():
                color_print(Colors.GREEN, " Here is the result:")
                print(indent(str(from_db_cursor(self.c)), 2))
            else:
                self.conn.commit()
                color_print(Colors.GREEN, " Successfully committed the query.")
        except Exception as e:
            self.clear()
            print("\n  You entered:")
            print(indent(command, 2))
            print("\n  Error happened when executing the above command:")
            color_print(Colors.RED, indent(str(e), 1))
        finally:
            spinner.stop()

    def view_all_records(self):
        tables = list(
            map(lambda t: t[0], self.c.execute("select name from sqlite_master where type = 'table'").fetchall()))
        if not tables:
            self.flash("There is no Table in " + self.db_path)
            self.clear()
            return
        row_counts = {t: self.c.execute("SELECT COUNT(*) FROM " + t).fetchone()[0] for t in tables}
        table_idx = 0
        row_idx = 0
        row_limit = 20
        while 1:
            total_rows = math.ceil(row_counts[tables[table_idx]] / row_limit)
            print(f"\n  Viewing {self.db_path} (hit {Colors.CYAN}Enter{Colors.ENDC} to exit)")
            color_print(Colors.BLUE, " Table:", tables[table_idx],
                        f'\t\tpage {row_idx + 1} / {total_rows}', '\n')
            arrow = self.view_table(tables[table_idx], row_limit, row_idx * row_limit)
            if arrow in {'left', 'right'}:
                old_table_idx = table_idx
                table_idx = (table_idx + (1 if arrow == 'right' else -1)) % len(tables)
                row_idx = 0
                self.flash(f"Switched from Table {tables[old_table_idx]} to Table {tables[table_idx]}")
            elif arrow in {'up', 'down'}:
                old_row_idx = row_idx
                row_idx = (row_idx + (1 if arrow == 'down' else -1)) % total_rows
                self.flash(f"Switched from page {old_row_idx + 1} to {row_idx + 1}")
            else:
                self.flash(f"Exited viewing table {tables[table_idx]}")
                self.clear()
                return
            self.clear()

    def view_table(self, table_name, row_limit=20, offset=0):
        self.c.execute("SELECT * FROM " + table_name + ' LIMIT ? OFFSET ?', [row_limit, offset])
        print(indent(str(from_db_cursor(self.c)), 2))
        color_print(Colors.BLUE, '\n', ' use up or down arrow to load more or less')
        color_print(Colors.BLUE, ' use left and right arrow to switch table')
        return get_arrow_input()
