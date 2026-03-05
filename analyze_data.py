import pandas as pd

# Load processed data
df = pd.read_csv('data/processed_features.csv')

print("="*60)
print("VORTEX DATA STATISTICS")
print("="*60)
print(f"\n📊 Total Events: {len(df):,}")
print(f"👥 Unique Users: {df['user_id'].nunique()}")
print(f"📅 Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
print(f"\n🚨 Anomalies (Ground Truth): {df['anomaly_flag_truth'].sum():,} ({df['anomaly_flag_truth'].sum()/len(df)*100:.1f}%)")
print(f"✅ Normal Events: {(df['anomaly_flag_truth']==0).sum():,} ({(df['anomaly_flag_truth']==0).sum()/len(df)*100:.1f}%)")

# Calculate risk levels from anomaly scores
q_high = df['anomaly_score'].quantile(0.95)
q_low = df['anomaly_score'].quantile(0.75)

def categorize_risk(score):
    if score >= q_high:
        return "High"
    elif score >= q_low:
        return "Medium"
    else:
        return "Low"

df['risk_level'] = df['anomaly_score'].apply(categorize_risk)

print(f"\n📈 Risk Level Distribution:")
print(df['risk_level'].value_counts().to_string())

print(f"\n👤 Events per User (Statistics):")
events_per_user = df.groupby('user_id').size()
print(f"   Mean: {events_per_user.mean():.1f}")
print(f"   Median: {events_per_user.median():.1f}")
print(f"   Min: {events_per_user.min()}")
print(f"   Max: {events_per_user.max()}")

print(f"\n🔝 Top 10 Users by Event Count:")
print(events_per_user.sort_values(ascending=False).head(10).to_string())

print(f"\n📋 Available Columns ({len(df.columns)}):")
for i, col in enumerate(df.columns, 1):
    print(f"   {i}. {col}")

print("\n" + "="*60)
