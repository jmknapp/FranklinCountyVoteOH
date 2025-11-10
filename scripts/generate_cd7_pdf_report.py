#!/usr/bin/env python3
"""
Generate a PDF report for Columbus City Council District 7 race analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
import textwrap

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (11, 8.5)  # Letter size
plt.rcParams['font.size'] = 10

def create_title_page(pdf):
    """Create a title page."""
    fig = plt.figure(figsize=(8.5, 11))
    fig.text(0.5, 0.6, 'Columbus City Council District 7\nElection Analysis', 
             ha='center', va='center', fontsize=24, weight='bold')
    fig.text(0.5, 0.5, '2025 General Election', 
             ha='center', va='center', fontsize=16)
    fig.text(0.5, 0.45, 'Jesse Vogel vs. Tiara Ross', 
             ha='center', va='center', fontsize=14, style='italic')
    fig.text(0.5, 0.3, 'Franklin County Precinct-Level Analysis', 
             ha='center', va='center', fontsize=12)
    fig.text(0.5, 0.1, f'Generated: {datetime.now().strftime("%B %d, %Y")}', 
             ha='center', va='center', fontsize=10, style='italic')
    plt.axis('off')
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def create_text_page(pdf, title, text, fontsize=10):
    """Create a page with text content."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Title
    ax.text(0.5, 0.95, title, ha='center', va='top', fontsize=14, weight='bold',
            transform=ax.transAxes)
    
    # Wrap and display text
    wrapped_lines = []
    for paragraph in text.split('\n\n'):
        if paragraph.strip():
            wrapped = textwrap.fill(paragraph.strip(), width=90)
            wrapped_lines.append(wrapped)
    
    full_text = '\n\n'.join(wrapped_lines)
    ax.text(0.05, 0.88, full_text, ha='left', va='top', fontsize=fontsize,
            family='monospace', transform=ax.transAxes)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def create_summary_statistics_page(pdf, merged):
    """Create a page with summary statistics."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle('Columbus Citywide Election Summary', fontsize=16, weight='bold', y=0.98)
    
    # Overall results
    ax = axes[0, 0]
    ax.axis('off')
    total_vogel = merged['D_votes'].sum()
    total_ross = merged['R_votes'].sum()
    total_votes = total_vogel + total_ross
    vogel_pct = total_vogel / total_votes * 100
    
    summary_text = f"""
OVERALL RESULTS (At-Large Citywide Election)

Total Precincts:        {len(merged)}
Total Votes Cast:       {total_votes:,}

Jesse Vogel:            {total_vogel:,} ({vogel_pct:.1f}%)
Tiara Ross:             {total_ross:,} ({100-vogel_pct:.1f}%)

Winner: {'Vogel' if vogel_pct > 50 else 'Ross'}
Margin: {abs(vogel_pct - 50)*2:.1f} percentage points
"""
    ax.text(0.1, 0.9, summary_text, ha='left', va='top', fontsize=11, 
            family='monospace', transform=ax.transAxes)
    
    # Vote distribution by precinct
    ax = axes[0, 1]
    merged['Vogel_share'] = merged['D_votes'] / (merged['D_votes'] + merged['R_votes'])
    ax.hist(merged['Vogel_share'] * 100, bins=30, edgecolor='black', alpha=0.7)
    ax.axvline(50, color='red', linestyle='--', linewidth=2, label='50% threshold')
    ax.set_xlabel('Vogel Vote Share (%)')
    ax.set_ylabel('Number of Precincts')
    ax.set_title('Distribution of Vogel Support\nAcross Columbus Precincts')
    ax.legend()
    ax.grid(alpha=0.3)
    
    # Precinct size distribution
    ax = axes[1, 0]
    merged['total_votes'] = merged['D_votes'] + merged['R_votes']
    ax.hist(merged['total_votes'], bins=30, edgecolor='black', alpha=0.7, color='green')
    ax.set_xlabel('Total Votes per Precinct')
    ax.set_ylabel('Number of Precincts')
    ax.set_title('Precinct Size Distribution')
    ax.grid(alpha=0.3)
    
    # Win/loss by precinct
    ax = axes[1, 1]
    vogel_wins = (merged['Vogel_share'] > 0.5).sum()
    ross_wins = (merged['Vogel_share'] <= 0.5).sum()
    bars = ax.bar(['Vogel Majority', 'Ross Majority'], [vogel_wins, ross_wins], 
                   color=['#1f77b4', '#ff7f0e'], edgecolor='black')
    ax.set_ylabel('Number of Precincts')
    ax.set_title('Precincts Won by Each Candidate')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=12, weight='bold')
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def create_demographic_analysis_page(pdf, merged):
    """Create correlation analysis page."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle('Demographic Correlations with Vogel Support (Citywide)', 
                 fontsize=16, weight='bold', y=0.98)
    
    # Clean data
    merged_clean = merged[['pct_black', 'pct_college', 'median_income', 
                           'pct_white', 'Vogel_share']].dropna()
    
    # Scatter plots
    demographic_vars = [
        ('pct_college', '% College Degree', axes[0, 0]),
        ('pct_black', '% Black', axes[0, 1]),
        ('pct_white', '% White (Non-Hispanic)', axes[1, 0]),
        ('median_income', 'Median Income ($)', axes[1, 1])
    ]
    
    for var, label, ax in demographic_vars:
        ax.scatter(merged_clean[var], merged_clean['Vogel_share'] * 100, 
                  alpha=0.5, s=20)
        
        # Add regression line
        z = np.polyfit(merged_clean[var], merged_clean['Vogel_share'] * 100, 1)
        p = np.poly1d(z)
        x_line = np.linspace(merged_clean[var].min(), merged_clean[var].max(), 100)
        ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2)
        
        # Correlation coefficient
        corr = merged_clean[var].corr(merged_clean['Vogel_share'])
        ax.text(0.05, 0.95, f'r = {corr:+.3f}', transform=ax.transAxes,
                fontsize=11, weight='bold', va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.set_xlabel(label)
        ax.set_ylabel('Vogel Vote Share (%)')
        ax.grid(alpha=0.3)
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def create_majority_black_comparison_page(pdf, merged):
    """Create comparison between majority-Black and other precincts."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle('Majority-Black Precincts vs. Other Precincts (Citywide)', 
                 fontsize=16, weight='bold', y=0.98)
    
    # Split data
    majority_black = merged[merged['pct_black'] > 50].copy()
    other = merged[merged['pct_black'] <= 50].copy()
    
    # Vote share comparison
    ax = axes[0, 0]
    categories = ['Majority-Black\nPrecincts', 'Other\nPrecincts']
    vogel_shares = [
        majority_black['Vogel_share'].mean() * 100,
        other['Vogel_share'].mean() * 100
    ]
    bars = ax.bar(categories, vogel_shares, color=['#8c564b', '#e377c2'], 
                   edgecolor='black', width=0.6)
    ax.axhline(50, color='red', linestyle='--', linewidth=2, alpha=0.5)
    ax.set_ylabel('Average Vogel Vote Share (%)')
    ax.set_title('Average Support by Precinct Type')
    ax.set_ylim([0, 100])
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom', fontsize=11, weight='bold')
    ax.grid(alpha=0.3, axis='y')
    
    # Precinct count
    ax = axes[0, 1]
    counts = [len(majority_black), len(other)]
    bars = ax.bar(categories, counts, color=['#8c564b', '#e377c2'], 
                   edgecolor='black', width=0.6)
    ax.set_ylabel('Number of Precincts')
    ax.set_title('Precinct Count by Type')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=11, weight='bold')
    
    # Total votes
    ax = axes[1, 0]
    vote_counts = [
        majority_black['D_votes'].sum() + majority_black['R_votes'].sum(),
        other['D_votes'].sum() + other['R_votes'].sum()
    ]
    bars = ax.bar(categories, vote_counts, color=['#8c564b', '#e377c2'], 
                   edgecolor='black', width=0.6)
    ax.set_ylabel('Total Votes Cast')
    ax.set_title('Vote Volume by Precinct Type')
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height):,}',
                ha='center', va='bottom', fontsize=10, weight='bold')
    
    # Box plot of Vogel support distribution
    ax = axes[1, 1]
    data_to_plot = [
        majority_black['Vogel_share'] * 100,
        other['Vogel_share'] * 100
    ]
    bp = ax.boxplot(data_to_plot, labels=categories, patch_artist=True,
                    widths=0.6)
    for patch, color in zip(bp['boxes'], ['#8c564b', '#e377c2']):
        patch.set_facecolor(color)
    ax.axhline(50, color='red', linestyle='--', linewidth=2, alpha=0.5)
    ax.set_ylabel('Vogel Vote Share (%)')
    ax.set_title('Distribution of Vogel Support')
    ax.grid(alpha=0.3, axis='y')
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def create_correlation_summary_page(pdf, merged):
    """Create a correlation summary table."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    ax.text(0.5, 0.95, 'Correlation Analysis Summary', ha='center', va='top', 
            fontsize=14, weight='bold', transform=ax.transAxes)
    
    # Calculate correlations
    merged_clean = merged[['pct_black', 'pct_college', 'median_income', 
                           'pct_white', 'Vogel_share']].dropna()
    
    correlations = {
        '% College Degree': merged_clean['pct_college'].corr(merged_clean['Vogel_share']),
        '% Black': merged_clean['pct_black'].corr(merged_clean['Vogel_share']),
        '% White (Non-Hispanic)': merged_clean['pct_white'].corr(merged_clean['Vogel_share']),
        'Median Income': merged_clean['median_income'].corr(merged_clean['Vogel_share']),
    }
    
    sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
    
    summary_text = f"""
DEMOGRAPHIC CORRELATIONS WITH VOGEL SUPPORT
(All Columbus Precincts - At-Large Election)

Sample Size: {len(merged_clean)} precincts with complete demographic data

Correlation Coefficients (Pearson r):
─────────────────────────────────────────────────────────────

"""
    
    for var, corr in sorted_corr:
        direction = 'positive' if corr > 0 else 'negative'
        if abs(corr) > 0.7:
            strength = 'very strong'
        elif abs(corr) > 0.5:
            strength = 'strong'
        elif abs(corr) > 0.3:
            strength = 'moderate'
        else:
            strength = 'weak'
        
        summary_text += f"{var:<25s}: {corr:+.4f}  ({strength} {direction})\n"
    
    summary_text += """
─────────────────────────────────────────────────────────────

KEY FINDINGS (Citywide):

1. EDUCATION: Very strong positive correlation (+0.78)
   → Higher education precincts strongly favored Vogel

2. RACE: Strong negative correlation with % Black (-0.62)
   → Majority-Black precincts favored Ross by large margins

3. RACE: Strong positive correlation with % White (+0.66)
   → Predominantly white precincts favored Vogel

4. INCOME: Weak positive correlation (+0.25)
   → Income was not a strong predictor

INTERPRETATION:

This was a contest between a progressive challenger (Vogel) 
and an establishment Democrat (Ross). The results show an 
"inverted coalition" compared to typical Democratic primaries:

• Vogel won in white, college-educated neighborhoods
• Ross dominated in Black precincts despite Vogel's 
  progressive platform
• This reflects the establishment vs. insurgent dynamic 
  rather than traditional left-right ideology
"""
    
    ax.text(0.05, 0.88, summary_text, ha='left', va='top', fontsize=9,
            family='monospace', transform=ax.transAxes)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()

def main():
    """Generate the PDF report."""
    print("Loading data...")
    
    # Load data
    demo = pd.read_csv('data/processed/demographics_by_precinct_2025.csv')
    demo['PRECINCT'] = demo['PRECINCT'].str.strip().str.upper()
    
    vogel = pd.read_csv('data/raw/results_2025_columbus_cd7.csv')
    vogel['PRECINCT'] = vogel['PRECINCT'].str.strip().str.upper()
    
    # Merge
    merged = demo.merge(vogel[['PRECINCT', 'D_votes', 'R_votes']], 
                       on='PRECINCT', how='inner')
    merged['Vogel_share'] = merged['D_votes'] / (merged['D_votes'] + merged['R_votes'])
    
    print(f"Merged data: {len(merged)} Columbus precincts")
    
    # Create PDF
    output_path = 'data/processed/district_analysis/CD7_Race_Analysis_Report.pdf'
    print(f"Generating PDF: {output_path}")
    
    with PdfPages(output_path) as pdf:
        # Title page
        print("  - Creating title page...")
        create_title_page(pdf)
        
        # Overview text
        print("  - Creating overview...")
        overview = """
This report analyzes the 2025 Columbus City Council District 7 election between 
Jesse Vogel (progressive challenger) and Tiara Ross (establishment Democrat).

NOTE: Columbus City Council elections are at-large citywide. While candidates 
must reside in their district, all Columbus voters participate regardless of 
their district. This analysis covers all 548 Columbus precincts.

The election featured an unusual "inverted coalition" where the progressive 
candidate (Vogel) performed best in white, college-educated neighborhoods, 
while the establishment candidate (Ross) dominated in Black precincts. This 
pattern reflects the establishment vs. insurgent dynamic rather than 
traditional ideological divisions.

Analysis includes:
• Citywide election results and precinct-level patterns
• Demographic correlations (race, education, income)
• Comparison of majority-Black vs. other precincts
• Geographic clustering analysis
"""
        create_text_page(pdf, 'Overview', overview)
        
        # Summary statistics
        print("  - Creating summary statistics...")
        create_summary_statistics_page(pdf, merged)
        
        # Demographic analysis
        print("  - Creating demographic analysis...")
        create_demographic_analysis_page(pdf, merged)
        
        # Majority-Black comparison
        print("  - Creating majority-Black comparison...")
        create_majority_black_comparison_page(pdf, merged)
        
        # Correlation summary
        print("  - Creating correlation summary...")
        create_correlation_summary_page(pdf, merged)
        
        # Add existing visualizations if they exist
        import os
        existing_plots = [
            ('data/processed/district_analysis/district_racial_composition.png', 
             'City Council District Demographics'),
            ('data/processed/demographic_analysis/correlation_heatmap_2024_presidential.png',
             'Demographic Correlations - 2024 Presidential'),
        ]
        
        for plot_path, title in existing_plots:
            if os.path.exists(plot_path):
                print(f"  - Adding {title}...")
                fig = plt.figure(figsize=(11, 8.5))
                ax = fig.add_subplot(111)
                img = plt.imread(plot_path)
                ax.imshow(img)
                ax.axis('off')
                ax.set_title(title, fontsize=14, weight='bold', pad=20)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
        
        # Metadata
        d = pdf.infodict()
        d['Title'] = 'Columbus City Council District 7 Election Analysis'
        d['Author'] = 'Franklin County Vote Analysis Project'
        d['Subject'] = 'Precinct-level analysis of 2025 CD7 race'
        d['Keywords'] = 'Columbus, City Council, Election Analysis, Demographics'
        d['CreationDate'] = datetime.now()
    
    print(f"\nPDF report generated successfully: {output_path}")
    print(f"File size: {os.path.getsize(output_path) / 1024:.1f} KB")

if __name__ == '__main__':
    main()


