import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# 1. Load the data
file_name = "experiment_results3.csv"
try:
    df = pd.read_csv(file_name)
except FileNotFoundError:
    print(f"🚨 Error: '{file_name}' not found. Please run your Streamlit app and complete a few queries first!")
    sys.exit()

# 2. Validate the data
if "verification_time_seconds" not in df.columns:
    print("🚨 Error: 'verification_time_seconds' column is missing. Check your CSV file.")
    sys.exit()

# Drop any rows where the timer might have failed or is empty
df = df.dropna(subset=['verification_time_seconds'])

if len(df) == 0:
    print("⚠️ Your dataset is currently empty. Do some test runs in the app first!")
    sys.exit()

# 3. Set up the IEEE-style plot aesthetics
sns.set_theme(style="whitegrid")
# 7x6 inches scales down perfectly to fit within a single IEEE column
plt.figure(figsize=(7, 6)) 

# Define colors to match your previous charts (Red = Bad/Control, Green = Good/Experimental)
custom_palette = {
    'Blind Mode (Control)': '#e74c3c', 
    'Source-Grounded (Experimental)': '#2ecc71'
}

# 4. Generate the Box-and-Whisker Plot
ax = sns.boxplot(
    x="verification_mode",
    y="verification_time_seconds",
    data=df,
    palette=custom_palette,
    width=0.5,
    linewidth=2,
    fliersize=0 # We hide outliers here because the stripplot will show them
)

# 5. Overlay individual data points (The "HCI Researcher" trick)
sns.stripplot(
    x="verification_mode",
    y="verification_time_seconds",
    data=df,
    color="#2c3e50", # Dark grey dots
    alpha=0.6,       # Semi-transparent
    jitter=True,     # Spreads dots out horizontally so they don't overlap
    size=6
)

# 6. Formatting and Labels
plt.title("Verification Latency by Interface Mode", pad=15, fontweight='bold', fontsize=14)
plt.ylabel("Verification Time (Seconds)", fontweight='bold', fontsize=12)
plt.xlabel("Interface Mode", fontweight='bold', fontsize=12)

plt.xticks(fontsize=11)
plt.yticks(fontsize=11)

# Ensure nothing gets cropped out
plt.tight_layout()

# 7. Save in High-Resolution for the Paper
output_file = "verification_time_boxplot.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')

print(f"\n✅ Success! Saved '{output_file}' at 300 DPI.")
print("You can now insert this directly into the Results section of your LaTeX document.")

plt.show()