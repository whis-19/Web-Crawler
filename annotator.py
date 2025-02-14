from crawler import *  


# Google Gemini API
API_KEY = "AIzaSyDXrCN8ShpZn0R_or-g4-1aGMjzXFm9wdE"  # Replace with your actual API key
genai.configure(api_key=API_KEY)

# Categories
CATEGORIES = [
    "Deep Learning",
    "Natural Language Processing",
    "Computer Vision",
    "Reinforcement Learning",
    "Optimization & Theory"
]

# Function to classify a paper
def classify_paper(title, abstract):
    """Ask Gemini to classify the paper with rate limiting."""
    prompt = f"""
    Given the following research paper details:
    Title: {title}
    Abstract: {abstract}

    Classify this paper into one of these categories: {', '.join(CATEGORIES)}.
    Just return the category name.
    """
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        category = response.text.strip()
        return category if category in CATEGORIES else "Uncategorized"
    except Exception as e:
        print(f"Error classifying paper: {e}")
        if "Quota" in str(e) or "rate limit" in str(e).lower():  # Check for rate limit errors
            print("Rate limit encountered.  Waiting before retrying...")
            time.sleep(60) # Wait for a minute before retrying
            return classify_paper(title, abstract) # Retry the same paper
        else:
            raise  # Re-raise other exceptions


# Function to annotate a CSV file
def annotate_csv(file_path):
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as input_file:
            reader = csv.reader(input_file)
            data = list(reader)

        # Check if 'Category' column exists
        if len(data) > 0 and data[0][-1] != "Category":
            data[0].append("Category")  # Add 'Category' column to CSV

        for i, row in enumerate(data[1:]):  # Iterate with index for better error handling
            if len(row) < 5:  # Ensure row has enough columns
                row.append("Missing Data")
                continue

            title = row[2]  # Column 3 (Title)
            abstract = row[4]  # Column 5 (Abstract)

            if not title or not abstract:
                category = "Missing Data"
            else:
                try:
                    category = classify_paper(title, abstract)
                except Exception as e:
                    print(f"Error on row {i+2}: {e}") # Print the row number where the error occurred
                    category = "Error" # Mark the row as error
                    
            row.append(category)

        # Save annotated data
        with open(file_path, 'w', newline='', encoding='utf-8') as output_file:
            writer = csv.writer(output_file)
            writer.writerows(data)

        print(f"✅ Annotation complete for {os.path.basename(file_path)}!")

    except Exception as e:  # Catch file-related errors
        print(f"Error processing file {file_path}: {e}")




def annotate_all_csvs():
    meta_results_dir = "./MetaData_Results"
    if not os.path.exists(meta_results_dir):
        print("MetaData_Results directory not found.  Make sure crawler_main() has run.")
        return
    #Loop to iterate through multiple CSVs
    for filename in os.listdir(meta_results_dir):
        if filename.endswith(".csv"):
            file_path = os.path.join(meta_results_dir, filename)
            annotate_csv(file_path)

def main():
    crawler_main()
    annotate_all_csvs()


