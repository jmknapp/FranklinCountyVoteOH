#!/usr/bin/env python3
"""
Analyze correlations between demographics and voting patterns.

Produces correlation matrices, scatter plots, and identifies demographically
distinct voting blocs.
"""

import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'
OUTPUT_DIR = PROCESSED_DIR / 'demographic_analysis'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_voting_and_demographics(vote_csv, demo_csv):
    """Load and merge voting results with demographics."""
    logger.info(f"Loading voting data from {vote_csv}")
    votes = pd.read_csv(vote_csv)
    votes['PRECINCT'] = votes['PRECINCT'].str.strip().str.upper()
    
    logger.info(f"Loading demographics from {demo_csv}")
    demographics = pd.read_csv(demo_csv)
    demographics['PRECINCT'] = demographics['PRECINCT'].str.strip().str.upper()
    
    # Calculate Democratic share
    votes['D_share'] = votes['D_votes'] / (votes['D_votes'] + votes['R_votes'])
    
    # Merge
    merged = votes.merge(demographics, on='PRECINCT', how='inner')
    
    logger.info(f"Merged data: {len(merged)} precincts")
    
    return merged


def clean_demographics(df):
    """Clean demographic data (handle missing values, outliers)."""
    # Replace negative median incomes with NaN (likely missing data)
    df.loc[df['median_income'] < 0, 'median_income'] = np.nan
    
    # Remove precincts with no votes
    df = df[(df['D_votes'] > 0) | (df['R_votes'] > 0)].copy()
    
    return df


def compute_correlations(df, race_label):
    """Compute correlations between demographics and D_share."""
    demo_cols = ['median_income', 'median_age', 'pct_college', 
                 'pct_white', 'pct_black', 'pct_hispanic', 'total_pop']
    
    # Remove rows with missing values for correlation
    df_clean = df[['D_share'] + demo_cols].dropna()
    
    logger.info(f"Computing correlations for {race_label} ({len(df_clean)} precincts)")
    
    # Compute correlation matrix
    corr_matrix = df_clean.corr()
    
    # Extract correlations with D_share
    d_share_corr = corr_matrix['D_share'].drop('D_share').sort_values(ascending=False)
    
    logger.info(f"\nCorrelations with Democratic vote share ({race_label}):")
    for var, corr in d_share_corr.items():
        logger.info(f"  {var:20s}: {corr:+.3f}")
    
    # Create correlation heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title(f'Demographic Correlations - {race_label}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / f'correlation_heatmap_{race_label.replace(" ", "_").lower()}.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"✓ Saved heatmap to {output_path}")
    plt.close(fig)
    
    return d_share_corr


def create_scatter_plots(df, race_label):
    """Create scatter plots of D_share vs key demographic variables."""
    demo_vars = [
        ('median_income', 'Median Household Income', '$'),
        ('pct_college', '% College Degree', '%'),
        ('pct_white', '% White (Non-Hispanic)', '%'),
        ('pct_black', '% Black', '%'),
    ]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    axes = axes.flatten()
    
    for idx, (var, label, unit) in enumerate(demo_vars):
        ax = axes[idx]
        
        # Remove missing data
        plot_data = df[[var, 'D_share']].dropna()
        
        # Scatter plot
        ax.scatter(plot_data[var], plot_data['D_share'] * 100, 
                   alpha=0.5, s=30, color='steelblue')
        
        # Add regression line
        if len(plot_data) > 5:
            z = np.polyfit(plot_data[var], plot_data['D_share'] * 100, 1)
            p = np.poly1d(z)
            x_line = np.linspace(plot_data[var].min(), plot_data[var].max(), 100)
            ax.plot(x_line, p(x_line), 'r--', linewidth=2, alpha=0.8)
            
            # Calculate R²
            corr = plot_data[var].corr(plot_data['D_share'])
            r_squared = corr ** 2
            ax.text(0.05, 0.95, f'R² = {r_squared:.3f}\nr = {corr:+.3f}',
                    transform=ax.transAxes, fontsize=10,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.set_xlabel(label, fontsize=11)
        ax.set_ylabel('Democratic Vote Share (%)', fontsize=11)
        ax.set_title(f'{label} vs Democratic Support', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 100)
    
    fig.suptitle(f'Demographic Factors vs Democratic Vote Share\n{race_label}', 
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / f'scatter_plots_{race_label.replace(" ", "_").lower()}.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"✓ Saved scatter plots to {output_path}")
    plt.close(fig)


def identify_demographic_blocs(df, race_label):
    """Identify distinct demographic voting blocs."""
    logger.info(f"\nIdentifying demographic voting blocs for {race_label}...")
    
    # Clean data
    analysis_cols = ['median_income', 'pct_college', 'pct_white', 'pct_black', 'D_share']
    df_clean = df[analysis_cols + ['PRECINCT']].dropna()
    
    # Define demographic categories
    income_median = df_clean['median_income'].median()
    college_median = df_clean['pct_college'].median()
    
    df_clean['income_category'] = df_clean['median_income'].apply(
        lambda x: 'High Income' if x > income_median else 'Low Income'
    )
    df_clean['education_category'] = df_clean['pct_college'].apply(
        lambda x: 'High Education' if x > college_median else 'Low Education'
    )
    df_clean['racial_majority'] = df_clean.apply(
        lambda row: 'Majority White' if row['pct_white'] > 60 
                    else ('Majority Black' if row['pct_black'] > 40 else 'Diverse'),
        axis=1
    )
    
    # Group by demographic categories
    grouped = df_clean.groupby(['income_category', 'education_category', 'racial_majority']).agg({
        'D_share': 'mean',
        'PRECINCT': 'count'
    }).rename(columns={'PRECINCT': 'num_precincts'})
    
    grouped['D_share_pct'] = grouped['D_share'] * 100
    grouped = grouped.sort_values('D_share_pct', ascending=False)
    
    logger.info(f"\nDemographic voting blocs ({race_label}):")
    logger.info(f"{'Demographic Group':<50s} {'Precincts':>10s} {'D Share':>10s}")
    logger.info("-" * 72)
    
    for (income, education, race), row in grouped.iterrows():
        group_label = f"{income}, {education}, {race}"
        logger.info(f"{group_label:<50s} {row['num_precincts']:>10.0f} {row['D_share_pct']:>10.1f}%")
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Prepare data for grouped bar chart
    grouped_reset = grouped.reset_index()
    grouped_reset['group_label'] = (grouped_reset['income_category'] + '\n' + 
                                     grouped_reset['education_category'] + '\n' + 
                                     grouped_reset['racial_majority'])
    
    # Sort by D_share for clarity
    grouped_reset = grouped_reset.sort_values('D_share_pct', ascending=True)
    
    bars = ax.barh(range(len(grouped_reset)), grouped_reset['D_share_pct'], 
                    color=grouped_reset['D_share_pct'].apply(
                        lambda x: plt.cm.RdBu(x / 100)
                    ))
    
    ax.set_yticks(range(len(grouped_reset)))
    ax.set_yticklabels(grouped_reset['group_label'], fontsize=9)
    ax.set_xlabel('Democratic Vote Share (%)', fontsize=12)
    ax.set_title(f'Democratic Support by Demographic Bloc - {race_label}', 
                 fontsize=14, fontweight='bold')
    ax.axvline(50, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.grid(axis='x', alpha=0.3)
    ax.set_xlim(0, 100)
    
    # Add vote count labels
    for idx, row in enumerate(grouped_reset.itertuples()):
        ax.text(row.D_share_pct + 2, idx, f"n={row.num_precincts:.0f}", 
                va='center', fontsize=8, color='black')
    
    plt.tight_layout()
    
    output_path = OUTPUT_DIR / f'demographic_blocs_{race_label.replace(" ", "_").lower()}.png'
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    logger.info(f"✓ Saved demographic blocs chart to {output_path}")
    plt.close(fig)


def main():
    """Analyze demographic correlations for key races."""
    logger.info("=" * 60)
    logger.info("DEMOGRAPHIC CORRELATION ANALYSIS")
    logger.info("=" * 60)
    
    demo_csv = PROCESSED_DIR / 'demographics_by_precinct_2025.csv'
    
    if not demo_csv.exists():
        logger.error(f"Demographics file not found: {demo_csv}")
        logger.error("Run: python scripts/aggregate_demographics_to_precincts.py")
        return 1
    
    # Analyze 2024 Presidential race
    vote_2024 = RAW_DIR / 'results_2024.csv'
    if vote_2024.exists():
        logger.info("\n" + "=" * 60)
        logger.info("ANALYZING: 2024 Presidential Election")
        logger.info("=" * 60)
        
        df = load_voting_and_demographics(vote_2024, demo_csv)
        df = clean_demographics(df)
        
        compute_correlations(df, "2024 Presidential")
        create_scatter_plots(df, "2024 Presidential")
        identify_demographic_blocs(df, "2024 Presidential")
    
    # Analyze 2023 Issue 1 (Abortion Rights)
    vote_2023 = RAW_DIR / 'results_2023_issue1.csv'
    if vote_2023.exists():
        logger.info("\n" + "=" * 60)
        logger.info("ANALYZING: 2023 Issue 1 (Abortion Rights)")
        logger.info("=" * 60)
        
        df = load_voting_and_demographics(vote_2023, demo_csv)
        df = clean_demographics(df)
        
        compute_correlations(df, "2023 Issue 1")
        create_scatter_plots(df, "2023 Issue 1")
        identify_demographic_blocs(df, "2023 Issue 1")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ DEMOGRAPHIC ANALYSIS COMPLETE")
    logger.info("=" * 60)
    logger.info(f"\nOutputs saved to: {OUTPUT_DIR}")
    logger.info(f"\nKey findings:")
    logger.info(f"  - Correlation heatmaps show relationships between demographics")
    logger.info(f"  - Scatter plots visualize demographic gradients")
    logger.info(f"  - Demographic blocs identify distinct voter groups")
    
    return 0


if __name__ == '__main__':
    exit(main())

