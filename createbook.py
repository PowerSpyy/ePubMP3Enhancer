import ebooklib
from ebooklib import epub
import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from tkinterhtml import HtmlFrame
from bs4 import BeautifulSoup
import shutil

allowed_chars = "1234567890-"

def validate(char, entry_value):
    return char in allowed_chars

class EPUBToJSONConverter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ePub to JSON Converter with MP3 Soundtracks")
        self.geometry("{0}x{1}+0+0".format(self.winfo_screenwidth(), self.winfo_screenheight()))

        self.book_json = None
        self.current_file_path = None
        self.current_page = 0
        self.current_chapter = 0
        self.lines_per_page = 20

        # Create GUI elements
        self.text_widget = ScrolledText(self, wrap='word', state='disabled')
        self.text_widget.pack(expand=1, fill='both')

        self.save_button = tk.Button(self, text="Save JSON", command=self.save_json, state=tk.DISABLED)
        self.save_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.load_button = tk.Button(self, text="Load ePub", command=self.load_epub)
        self.load_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.add_soundtrack_button = tk.Button(self, text="Add Soundtrack", command=self.add_soundtrack, state=tk.DISABLED)
        self.add_soundtrack_button.pack(side=tk.LEFT, padx=10, pady=10)

        vcmd = (self.register(validate), '%S', '%P')
        self.page_number_entry = tk.Entry(self, validate='key', validatecommand=vcmd)
        self.page_number_entry.pack(side=tk.LEFT, padx=10, pady=10)

        self.prev_page_button = tk.Button(self, text="Previous Page", command=self.show_previous_page, state=tk.DISABLED)
        self.prev_page_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.next_page_button = tk.Button(self, text="Next Page", command=self.show_next_page, state=tk.DISABLED)
        self.next_page_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.prev_chapter_button = tk.Button(self, text="Previous Chapter", command=self.show_previous_chapter, state=tk.DISABLED)
        self.prev_chapter_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.next_chapter_button = tk.Button(self, text="Next Chapter", command=self.show_next_chapter, state=tk.DISABLED)
        self.next_chapter_button.pack(side=tk.LEFT, padx=10, pady=10)

        # Page number display label
        self.page_number_label = tk.Label(self, text="Page: 1")
        self.page_number_label.pack(side=tk.LEFT, padx=10, pady=10)

        # Initialize HtmlFrame
        self.html_frame = HtmlFrame(self, horizontal_scrollbar="auto")
        self.html_frame.pack(expand=True, fill=tk.BOTH)

    def load_epub(self):
        file_path = filedialog.askopenfilename(filetypes=[("ePub files", "*.epub")])
        if file_path:
            self.current_file_path = file_path
            self.book_json = self.parse_epub(file_path)
            self.current_page = 0
            self.current_chapter = 0
            self.display_book()
            self.add_soundtrack_button.config(state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)
            self.prev_page_button.config(state=tk.NORMAL)
            self.next_page_button.config(state=tk.NORMAL)
            self.prev_chapter_button.config(state=tk.NORMAL)
            self.next_chapter_button.config(state=tk.NORMAL)
            self.update_page_number_display()

    def parse_epub(self, file_path):
        book = epub.read_epub(file_path)
        book_json = {
            "title": book.get_metadata('DC', 'title')[0][0],
            "author": book.get_metadata('DC', 'creator')[0][0],
            "soundtracks": {},  # Store all soundtracks globally
            "chapters": []
        }

        total_pages = 0  # Initialize total page counter

        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_body_content().decode('utf-8'), 'html.parser')
            text_data = str(soup)
            chapter_text = self.paginate_text(text_data)
            chapter = {
                "title": item.get_name() if item.get_name() else "Untitled Chapter",
                "text": chapter_text,
                "images": [img['src'] for img in soup.find_all('img')],
            }
            book_json["chapters"].append(chapter)

        return book_json

    def paginate_text(self, text_data):
        soup = BeautifulSoup(text_data, 'html.parser')
        paragraphs = soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'img'])
        pages = {}
        current_page = 1
        current_content = []

        for paragraph in paragraphs:
            current_content.append(str(paragraph))
            if len(current_content) >= self.lines_per_page:
                pages[current_page] = ''.join(current_content)
                current_page += 1
                current_content = []

        if current_content:
            pages[current_page] = ''.join(current_content)

        return pages

    def display_book(self):
        self.text_widget.config(state='normal')
        self.text_widget.delete(1.0, tk.END)
        if self.book_json and self.book_json["chapters"]:
            self.show_page()
        self.text_widget.config(state='disabled')

    def show_page(self):
        current_chapter = self.book_json["chapters"][self.current_chapter]
        pages = current_chapter["text"]
        page_content = pages.get(self.current_page + 1, "")
        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(page_content, 'html.parser')
        # Extract the text from parsed HTML
        plain_text = soup.get_text()
        # Insert the plain text into the text widget
        self.text_widget.config(state='normal')
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, page_content)
        self.text_widget.config(state='disabled')

        # Set HTML content in HtmlFrame
        self.html_frame.set_content(page_content)

        # Update page number display
        self.update_page_number_display()

    def show_previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
        else:
            if self.current_chapter > 0:
                self.current_chapter -= 1
                self.current_page = len(self.book_json["chapters"][self.current_chapter]["text"]) - 1
        self.display_book()

    def show_next_page(self):
        if self.book_json:
            current_chapter_text = self.book_json["chapters"][self.current_chapter]["text"]
            if self.current_page < len(current_chapter_text) - 1:
                self.current_page += 1
            else:
                if self.current_chapter < len(self.book_json["chapters"]) - 1:
                    self.current_chapter += 1
                    self.current_page = 0
            self.display_book()

    def show_previous_chapter(self):
        if self.current_chapter > 0:
            self.current_chapter -= 1
            self.current_page = 0
            self.display_book()

    def show_next_chapter(self):
        if self.current_chapter < len(self.book_json["chapters"]) - 1:
            self.current_chapter += 1
            self.current_page = 0
            self.display_book()

    def add_soundtrack(self):
        page_range = self.page_number_entry.get().strip()
        if '-' not in page_range:
            messagebox.showerror("Invalid Input", "Please enter a valid page range (e.g., 1-5).")
            return

        start_page, end_page = page_range.split('-')
        try:
            start_page = int(start_page)
            end_page = int(end_page)
        except ValueError:
            messagebox.showerror("Invalid Input", "Page numbers must be integers.")
            return
        max_page = 0
        for idx in range(len(self.book_json["chapters"])):
            max_page += len(self.book_json["chapters"][idx]["text"])

        if start_page > end_page or start_page < 1 or end_page > max_page:
            messagebox.showerror("Invalid Input", f"Invalid page range. Please enter a range between 1 and {max_page}.")
            return

        mp3_file = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if mp3_file:
            soundtrack_key = f"{start_page}-{end_page}"
            self.book_json["soundtracks"][soundtrack_key] = mp3_file
            messagebox.showinfo("Success", "Soundtrack added successfully!")

    def save_json(self):
        if not self.book_json:
            messagebox.showerror("Error", "No EPUB file loaded.")
            return

        folder_path = filedialog.askdirectory()
        if folder_path:
            title = self.book_json["title"]
            # Create a folder named after the title of the book within the chosen directory
            output_folder = os.path.join(folder_path, f'{title}_conversion')
            os.makedirs(output_folder, exist_ok=True)

            # Create a dictionary to store soundtracks for the book
            book_soundtracks = {}

            # Iterate through global soundtracks dictionary and copy files
            for key, mp3_file in self.book_json["soundtracks"].items():
                # Determine the chapter title and create a folder for each chapter
                chapter_title = self.book_json["chapters"][self.current_chapter]["title"]
                chapter_folder = os.path.join(output_folder, chapter_title.replace(" ", "_"))
                os.makedirs(chapter_folder, exist_ok=True)

                # Create relative path for the mp3 file
                mp3_filename = os.path.basename(mp3_file)
                relative_path = os.path.join(chapter_folder, mp3_filename)

                # Copy mp3 file to chapter folder
                shutil.copyfile(mp3_file, relative_path)

                # Store in book soundtracks dictionary
                book_soundtracks[key] = relative_path

            # Save the updated book JSON to a file
            self.book_json["soundtracks"] = book_soundtracks
            json_output_file = os.path.join(output_folder, 'book.json')
            with open(json_output_file, 'w') as f:
                json.dump(self.book_json, f, indent=4)

            messagebox.showinfo("Success", f"JSON file saved successfully in {json_output_file}")

    def update_page_number_display(self):
        total_pages = 0

        # Calculate total pages from previous chapters
        for idx in range(self.current_chapter):
            total_pages += len(self.book_json["chapters"][idx]["text"])

        # Add current page within the current chapter
        total_pages += self.current_page + 1

        self.page_number_label.config(text=f"Page: {total_pages}")


if __name__ == "__main__":
    app = EPUBToJSONConverter()
    app.mainloop()