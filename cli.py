import os
import sys
import time
import httpx

BASE_URL = "http://localhost:8000"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title):
    print(f"\n{'=' * 50}")
    print(f" {title.upper()}")
    print(f"{'=' * 50}\n")

def check_health():
    try:
        r = httpx.get(f"{BASE_URL}/health")
        if r.status_code == 200:
            return True
    except Exception:
        pass
    print("Cannot connect to the server. Please run 'uv run python main.py' in a separate terminal.")
    sys.exit(1)

def list_books():
    print_header("Library")
    r = httpx.get(f"{BASE_URL}/books")
    data = r.json()
    if data["total"] == 0:
        print("Your library is empty. Upload a book first!")
    else:
        for idx, book in enumerate(data["books"], 1):
            print(f"  {idx}. {book}")
    return data["books"]

def upload_book():
    print_header("Upload Book")
    filepath = input("Enter the path to your TXT, PDF, or EPUB file (e.g., test_book.txt):\n> ").strip()
    
    # Remove quotes if dragged and dropped
    filepath = filepath.strip('"').strip("'")
    
    if not os.path.exists(filepath):
        print(f"File not found at '{filepath}'.")
        return

    title = input("Enter a display title for the book (or leave blank to use filename):\n> ").strip()
    
    print("\nUploading and processing (parsing, chunking, embedding)... This might take a moment.")
    
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (os.path.basename(filepath), f)}
            data = {'book_title': title} if title else {}
            
            r = httpx.post(f"{BASE_URL}/upload", files=files, data=data, timeout=120.0)
            
            if r.status_code in [200, 201]:
                res = r.json()
                print(f"\n{res['message']}")
            else:
                print(f"\nError {r.status_code}: {r.json().get('detail', r.text)}")
    except Exception as e:
        print(f"\nRequest failed: {e}")

def query_books():
    print_header("Ask the AI")
    question = input("Enter your question:\n> ").strip()
    
    if len(question) < 3:
        print("Question too short.")
        return

    # Ask if they want to filter
    filter_choice = input("Filter by specific book? (y/N): ").strip().lower()
    book_ids = []
    if filter_choice == 'y':
        books = list_books()
        if books:
            choice = input("\nEnter the number of the book to query:\n> ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(books):
                    book_ids.append(books[idx])
                    print(f"Filtering search to: {books[idx]}")
                else:
                    print("Invalid choice, searching all books.")
            except ValueError:
                print("Invalid input, searching all books.")
    
    payload = {"question": question}
    if book_ids:
        payload["book_ids"] = book_ids

    print("\nAnalyzing library and generating answer with Groq...\n")
    try:
        r = httpx.post(f"{BASE_URL}/query", json=payload, timeout=60.0)
        
        if r.status_code == 200:
            res = r.json()
            print(f"ANSWER:\n{res['answer']}\n")
            print("-" * 50)
            print(f"Searched {res['books_searched']} books.")
            print("\nSOURCES:")
            for idx, source in enumerate(res['sources'], 1):
                print(f"\n  [SOURCE {idx}] {source['book_title']} (Page {source['page']} - {source['chapter']})")
                print(f"  Excerpt: {source['excerpt']}...")
        else:
            print(f"Error {r.status_code}: {r.json().get('detail', r.text)}")
    except Exception as e:
            print(f"\nRequest failed: {e}")

def view_concepts():
    print_header("Core Concepts")
    try:
        r = httpx.get(f"{BASE_URL}/concepts", timeout=30.0)
        if r.status_code == 200:
            data = r.json()
            if data["total_books"] == 0:
                print("No concepts extracted yet.")
            else:
                for book, concepts in data["books"].items():
                    print(f"\n{book}")
                    for c in concepts:
                        print(f"  • {c}")
        else:
            print(f"Error {r.status_code}: {r.json().get('detail', r.text)}")
    except Exception as e:
            print(f"\nRequest failed: {e}")

def main():
    clear_screen()
    print("Testing connection to FastAPI Server...")
    check_health()
    
    while True:
        print_header("RAG Backend Manual Testing CLI")
        print("1. Upload a Book")
        print("2. List all Books")
        print("3. View Core Concepts")
        print("4. Query the AI")
        print("5. Exit")
        print("-" * 50)
        
        choice = input("Select an option (1-5): ").strip()
        
        if choice == '1':
            upload_book()
        elif choice == '2':
            list_books()
        elif choice == '3':
            view_concepts()
        elif choice == '4':
            query_books()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")
        
        input("\nPress Enter to continue...")
        clear_screen()

if __name__ == "__main__":
    main()
