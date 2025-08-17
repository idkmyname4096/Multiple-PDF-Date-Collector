import re
from collections import defaultdict
from datetime import datetime, timedelta
import pdfplumber
import os

def fill_missing_dates(date_counts):
    # Fill missing dates between earliest and latest dates with zero counts.
    if not date_counts:
        return date_counts

    sorted_dates = sorted(date_counts.keys(), key=lambda x: datetime.strptime(x, "%d %b %Y"))
    start_date = datetime.strptime(sorted_dates[0], "%d %b %Y")
    end_date = datetime.strptime(sorted_dates[-1], "%d %b %Y")

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%d %b %Y")
        if date_str not in date_counts:
            date_counts[date_str] = 0
        current_date += timedelta(days=1)

    return date_counts

def extract_and_count_dates(text):
    # Extract dates
    date_pattern = r"(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})"
    
    date_counts = defaultdict(int)
    
    # Month normalization mapping
    month_mapping = {
        'jan': 'Jan', 'january': 'Jan', 'feb': 'Feb', 'february': 'Feb',
        'mar': 'Mar', 'march': 'Mar', 'apr': 'Apr', 'april': 'Apr',
        'may': 'May', 'jun': 'Jun', 'june': 'Jun', 'jul': 'Jul', 'july': 'Jul',
        'aug': 'Aug', 'august': 'Aug', 'sep': 'Sep', 'september': 'Sep',
        'oct': 'Oct', 'october': 'Oct', 'nov': 'Nov', 'november': 'Nov',
        'dec': 'Dec', 'december': 'Dec'
    }
    
    matches = re.finditer(date_pattern, text, re.IGNORECASE)
    for match in matches:
        day, month, year = match.groups()
        month = month_mapping.get(month.lower(), month.lower()[:3].capitalize())
        date_str = f"{int(day):02d} {month} {year}"
        date_counts[date_str] += 1
    
    return dict(date_counts)

def find_month_year_counts(date_counts):
    #Generate month-year and year counts
    month_year_counts = defaultdict(int)
    year_counts = defaultdict(int)
    
    for date_str, count in date_counts.items():
        date_obj = datetime.strptime(date_str, "%d %b %Y")
        
        month_year_str = date_obj.strftime("%b %Y")
        year_str = str(date_obj.year)
        
        month_year_counts[month_year_str] += count
        year_counts[year_str] += count
    
    return dict(month_year_counts), dict(year_counts)

def sort_date_dict(date_dict, date_format):
    #Sort date dictionaries by different formats
    if date_format == "%d %b %Y":
        return sorted(date_dict.items(), key=lambda x: datetime.strptime(x[0], date_format))
    elif date_format == "%b %Y":
        return sorted(date_dict.items(), key=lambda x: datetime.strptime(x[0], date_format))
    else:
        return sorted(date_dict.items(), key=lambda x: int(x[0]))

def format_output_date(date_str, input_format, output_format):
    if input_format == "year":
        return date_str
    return datetime.strptime(date_str, input_format).strftime(output_format)

def write_date_statistics(date_counts, output_file):
    month_year_counts, year_counts = find_month_year_counts(date_counts)
    
    with open(output_file, 'w') as f:
        output_lines = []

        sections = [
            {
                'data': date_counts,
                'input_format': "%d %b %Y",
                'output_format': "%d-%b-%Y",
                'sort_format': "%d %b %Y"
            },
            {
                'data': month_year_counts,
                'input_format': "%b %Y", 
                'output_format': "%b-%Y",
                'sort_format': "%b %Y"
            },
            {
                'data': year_counts,
                'input_format': "year",
                'output_format': "year",
                'sort_format': "year"
            }
        ]

        for i, section in enumerate(sections):
            sorted_items = sort_date_dict(section['data'], section['sort_format'])
            
            for date, count in sorted_items:
                formatted_date = format_output_date(date, section['input_format'], section['output_format'])
                output_lines.append(f"{formatted_date}\t{count}")
            
            if i < len(sections) - 1:  
                output_lines.append("")

        output_lines.extend([
            "-" * 40,
            f"Total unique dates: {len(date_counts)}",
            f"Total date mentions: {sum(date_counts.values())}"
        ])

        f.write('\n'.join(output_lines))

def combine_date_counts(counts_list):
    #Combine multiple date count dictionaries.
    combined = defaultdict(int)
    for counts in counts_list:
        for date, count in counts.items():
            combined[date] += count
    return dict(combined)

def analyze_pdf_list(pdf_file_paths, output_file_path):
    all_date_counts = []

    for pdf_path in pdf_file_paths:
        print(f"Analyzing dates in: {pdf_path}")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ''.join(page.extract_text() or '' for page in pdf.pages)
            
            date_counts = extract_and_count_dates(text)
            all_date_counts.append(date_counts)
            
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {str(e)}")

    combined_date_counts = combine_date_counts(all_date_counts)
    
    # Fills missing dates and write results
    combined_date_counts = fill_missing_dates(combined_date_counts)
    write_date_statistics(combined_date_counts, output_file_path)

if __name__ == "__main__":
    pdf_file_paths = [
        r"PDF PATH HERE"
    ]
    output_file_path = r"OUTPUT PATH HERE"

    analyze_pdf_list(pdf_file_paths, output_file_path)
    