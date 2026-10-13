from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from matplotlib.patches import Patch

OUT = Path(__file__).resolve().parents[1] / 'viz'
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'figure.facecolor': '#F7F4EF',
    'axes.facecolor': '#FBF9F5',
    'axes.edgecolor': '#2C3338',
    'axes.labelcolor': '#2C3338',
    'xtick.color': '#2C3338',
    'ytick.color': '#2C3338',
    'text.color': '#2C3338',
    'grid.color': '#D9D2C5',
    'grid.linestyle': '--',
    'grid.linewidth': 0.7,
    'font.size': 10,
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'figure.dpi': 140,
})

TEMP = '#C45C26'
CPU = '#1F6F5B'
LAST = '#1B4F72'
SENSOR = '#B08900'
META = '#3D5A5B'

sensors = [
    (1, 'temperature', 'floor'),
    (2, 'temperature', 'ceiling'),
    (3, 'temperature', 'floor'),
    (4, 'temperature', 'ceiling'),
]
dataset = dict(total_rows=1156, sensors=4, earliest='2026-10-12 21:33:54+00',
               latest='2026-10-13 21:33:54+00', avg_temperature=50.39, avg_cpu=0.5009)
readings = {1: 289, 2: 289, 3: 289, 4: 289}

avg_rows = [
    ("2026-10-12 21:30:00+00", 59.13, 0.5687),
    ("2026-10-12 22:00:00+00", 55.20, 0.5163),
    ("2026-10-12 22:30:00+00", 54.37, 0.4594),
    ("2026-10-12 23:00:00+00", 44.58, 0.4635),
    ("2026-10-12 23:30:00+00", 47.45, 0.4135),
    ("2026-10-13 00:00:00+00", 47.08, 0.4910),
    ("2026-10-13 00:30:00+00", 44.12, 0.4328),
    ("2026-10-13 01:00:00+00", 61.82, 0.4899),
    ("2026-10-13 01:30:00+00", 43.48, 0.4654),
    ("2026-10-13 02:00:00+00", 51.86, 0.4534),
    ("2026-10-13 02:30:00+00", 51.28, 0.4717),
    ("2026-10-13 03:00:00+00", 44.03, 0.5337),
    ("2026-10-13 03:30:00+00", 44.30, 0.4893),
    ("2026-10-13 04:00:00+00", 54.49, 0.5064),
    ("2026-10-13 04:30:00+00", 54.16, 0.5328),
    ("2026-10-13 05:00:00+00", 57.09, 0.5706),
    ("2026-10-13 05:30:00+00", 44.51, 0.4576),
    ("2026-10-13 06:00:00+00", 50.49, 0.5011),
    ("2026-10-13 06:30:00+00", 58.45, 0.4323),
    ("2026-10-13 07:00:00+00", 39.39, 0.6207),
    ("2026-10-13 07:30:00+00", 60.23, 0.4932),
    ("2026-10-13 08:00:00+00", 50.65, 0.5092),
    ("2026-10-13 08:30:00+00", 48.81, 0.5795),
    ("2026-10-13 09:00:00+00", 61.03, 0.5561),
    ("2026-10-13 09:30:00+00", 51.24, 0.4035),
    ("2026-10-13 10:00:00+00", 55.11, 0.5927),
    ("2026-10-13 10:30:00+00", 44.16, 0.4235),
    ("2026-10-13 11:00:00+00", 52.07, 0.5147),
    ("2026-10-13 11:30:00+00", 49.45, 0.4856),
    ("2026-10-13 12:00:00+00", 47.61, 0.5533),
    ("2026-10-13 12:30:00+00", 43.76, 0.4255),
    ("2026-10-13 13:00:00+00", 45.28, 0.5636),
    ("2026-10-13 13:30:00+00", 41.44, 0.5816),
    ("2026-10-13 14:00:00+00", 51.83, 0.4591),
    ("2026-10-13 14:30:00+00", 45.75, 0.4599),
    ("2026-10-13 15:00:00+00", 53.25, 0.4914),
    ("2026-10-13 15:30:00+00", 46.97, 0.5621),
    ("2026-10-13 16:00:00+00", 50.78, 0.5167),
    ("2026-10-13 16:30:00+00", 46.94, 0.4451),
    ("2026-10-13 17:00:00+00", 55.80, 0.3870),
    ("2026-10-13 17:30:00+00", 52.29, 0.4697),
    ("2026-10-13 18:00:00+00", 52.43, 0.6253),
    ("2026-10-13 18:30:00+00", 44.23, 0.5492),
    ("2026-10-13 19:00:00+00", 48.16, 0.5709),
    ("2026-10-13 19:30:00+00", 53.34, 0.4694),
    ("2026-10-13 20:00:00+00", 48.56, 0.4202),
    ("2026-10-13 20:30:00+00", 56.32, 0.5409),
    ("2026-10-13 21:00:00+00", 57.94, 0.5436),
    ("2026-10-13 21:30:00+00", 25.21, 0.3895),
]

last_rows = [
    ("2026-10-12 21:30:00+00", 59.13, 89.87, 0.5687),
    ("2026-10-12 22:00:00+00", 55.20, 85.07, 0.5163),
    ("2026-10-12 22:30:00+00", 54.37, 39.05, 0.4594),
    ("2026-10-12 23:00:00+00", 44.58, 32.92, 0.4635),
    ("2026-10-12 23:30:00+00", 47.45, 46.83, 0.4135),
    ("2026-10-13 00:00:00+00", 47.08, 96.85, 0.4910),
    ("2026-10-13 00:30:00+00", 44.12, 25.17, 0.4328),
    ("2026-10-13 01:00:00+00", 61.82, 79.11, 0.4899),
    ("2026-10-13 01:30:00+00", 43.48, 15.39, 0.4654),
    ("2026-10-13 02:00:00+00", 51.86, 83.34, 0.4534),
    ("2026-10-13 02:30:00+00", 51.28, 9.46, 0.4717),
    ("2026-10-13 03:00:00+00", 44.03, 4.23, 0.5337),
    ("2026-10-13 03:30:00+00", 44.30, 12.54, 0.4893),
    ("2026-10-13 04:00:00+00", 54.49, 94.83, 0.5064),
    ("2026-10-13 04:30:00+00", 54.16, 57.46, 0.5328),
    ("2026-10-13 05:00:00+00", 57.09, 85.96, 0.5706),
    ("2026-10-13 05:30:00+00", 44.51, 12.68, 0.4576),
    ("2026-10-13 06:00:00+00", 50.49, 62.72, 0.5011),
    ("2026-10-13 06:30:00+00", 58.45, 87.57, 0.4323),
    ("2026-10-13 07:00:00+00", 39.39, 86.95, 0.6207),
    ("2026-10-13 07:30:00+00", 60.23, 73.59, 0.4932),
    ("2026-10-13 08:00:00+00", 50.65, 51.68, 0.5092),
    ("2026-10-13 08:30:00+00", 48.81, 13.84, 0.5795),
    ("2026-10-13 09:00:00+00", 61.03, 66.99, 0.5561),
    ("2026-10-13 09:30:00+00", 51.24, 61.71, 0.4035),
    ("2026-10-13 10:00:00+00", 55.11, 88.93, 0.5927),
    ("2026-10-13 10:30:00+00", 44.16, 51.97, 0.4235),
    ("2026-10-13 11:00:00+00", 52.07, 80.13, 0.5147),
    ("2026-10-13 11:30:00+00", 49.45, 33.62, 0.4856),
    ("2026-10-13 12:00:00+00", 47.61, 39.00, 0.5533),
    ("2026-10-13 12:30:00+00", 43.76, 93.06, 0.4255),
    ("2026-10-13 13:00:00+00", 45.28, 63.84, 0.5636),
    ("2026-10-13 13:30:00+00", 41.44, 90.45, 0.5816),
    ("2026-10-13 14:00:00+00", 51.83, 18.06, 0.4591),
    ("2026-10-13 14:30:00+00", 45.75, 34.96, 0.4599),
    ("2026-10-13 15:00:00+00", 53.25, 42.38, 0.4914),
    ("2026-10-13 15:30:00+00", 46.97, 74.01, 0.5621),
    ("2026-10-13 16:00:00+00", 50.78, 64.70, 0.5167),
    ("2026-10-13 16:30:00+00", 46.94, 85.12, 0.4451),
    ("2026-10-13 17:00:00+00", 55.80, 85.51, 0.3870),
    ("2026-10-13 17:30:00+00", 52.29, 17.66, 0.4697),
    ("2026-10-13 18:00:00+00", 52.43, 63.72, 0.6253),
    ("2026-10-13 18:30:00+00", 44.23, 26.75, 0.5492),
    ("2026-10-13 19:00:00+00", 48.16, 92.77, 0.5709),
    ("2026-10-13 19:30:00+00", 53.34, 78.77, 0.4694),
    ("2026-10-13 20:00:00+00", 48.56, 29.66, 0.4202),
    ("2026-10-13 20:30:00+00", 56.32, 87.37, 0.5409),
    ("2026-10-13 21:00:00+00", 57.94, 55.11, 0.5436),
    ("2026-10-13 21:30:00+00", 25.21, 0.38, 0.3895),
]

def parse_ts(s):
    return datetime.fromisoformat(s.replace('+00', '+00:00'))

def style_time_axis(ax):
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=3))
    plt.setp(ax.get_xticklabels(), rotation=35, ha='right')
    ax.grid(True, axis='both', alpha=0.8)

fig, ax = plt.subplots(figsize=(8, 4.2))
labels = [f"#{sid}\n{loc}" for sid, typ, loc in sensors]
colors = ['#1F6F5B' if loc == 'floor' else '#C45C26' for _, _, loc in sensors]
bars = ax.bar(labels, [1]*4, color=colors, edgecolor='#2C3338', linewidth=0.6, width=0.55)
ax.set_ylim(0, 1.6)
ax.set_ylabel('Present')
ax.set_title('Verification: sensors registered')
ax.set_yticks([0, 1])
ax.set_yticklabels(['no', 'yes'])
for b, (sid, typ, loc) in zip(bars, sensors):
    ax.text(b.get_x() + b.get_width()/2, 1.08, typ, ha='center', va='bottom', fontsize=9)
ax.legend(handles=[Patch(facecolor='#1F6F5B', edgecolor='#2C3338', label='floor'),
                   Patch(facecolor='#C45C26', edgecolor='#2C3338', label='ceiling')],
          loc='upper right', frameon=False)
fig.tight_layout()
fig.savefig(OUT / '01-sensors.png', bbox_inches='tight')
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), gridspec_kw={'width_ratios': [1.1, 1]})
ax0, ax1 = axes
sids = list(readings.keys())
counts = [readings[s] for s in sids]
bars = ax0.bar([f'sensor {s}' for s in sids], counts, color=SENSOR, edgecolor='#2C3338', linewidth=0.6)
ax0.set_ylabel('Readings')
ax0.set_title('Readings per sensor')
ax0.set_ylim(0, max(counts) * 1.2)
ax0.grid(True, axis='y')
for b, c in zip(bars, counts):
    ax0.text(b.get_x()+b.get_width()/2, c + 5, str(c), ha='center', fontsize=9)
ax1.axis('off')
summary = (
    f"total_rows: {dataset['total_rows']}\n"
    f"sensors: {dataset['sensors']}\n"
    f"avg_temperature: {dataset['avg_temperature']}\n"
    f"avg_cpu: {dataset['avg_cpu']}\n"
    f"earliest: {dataset['earliest'][:16]} UTC\n"
    f"latest:   {dataset['latest'][:16]} UTC"
)
ax1.text(0.05, 0.55, 'Dataset summary', fontsize=13, fontweight='bold', transform=ax1.transAxes)
ax1.text(0.05, 0.12, summary, fontsize=11, family='monospace', transform=ax1.transAxes,
         verticalalignment='bottom',
         bbox=dict(boxstyle='round,pad=0.6', facecolor='#EFE8DC', edgecolor='#2C3338'))
fig.suptitle('Verification: simulated dataset', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(OUT / '02-dataset-summary.png', bbox_inches='tight')
plt.close(fig)

periods = [parse_ts(r[0]) for r in avg_rows]
temps = [r[1] for r in avg_rows]
cpus = [r[2] for r in avg_rows]
fig, ax_t = plt.subplots(figsize=(10.5, 4.8))
ax_c = ax_t.twinx()
l1, = ax_t.plot(periods, temps, color=TEMP, linewidth=2.0, marker='o', markersize=3.2, label='avg_temperature')
l2, = ax_c.plot(periods, cpus, color=CPU, linewidth=2.0, marker='s', markersize=3.0, label='avg_cpu')
ax_t.set_ylabel('Average temperature')
ax_c.set_ylabel('Average CPU')
ax_t.set_xlabel('Period (UTC), 30-minute buckets')
ax_t.set_title('Average temperature and CPU by 30-minute windows')
style_time_axis(ax_t)
ax_t.legend(handles=[l1, l2], loc='upper left', frameon=False)
fig.tight_layout()
fig.savefig(OUT / '03-avg-temp-cpu-30m.png', bbox_inches='tight')
plt.close(fig)

periods = [parse_ts(r[0]) for r in last_rows]
avg_t = [r[1] for r in last_rows]
last_t = [r[2] for r in last_rows]
cpus = [r[3] for r in last_rows]
fig, ax_t = plt.subplots(figsize=(10.5, 4.8))
ax_c = ax_t.twinx()
l1, = ax_t.plot(periods, avg_t, color=TEMP, linewidth=2.0, marker='o', markersize=3.0, label='avg_temperature')
l2, = ax_t.plot(periods, last_t, color=LAST, linewidth=1.6, linestyle='--', marker='^', markersize=3.2, label='last_temperature')
l3, = ax_c.plot(periods, cpus, color=CPU, linewidth=2.0, marker='s', markersize=3.0, label='avg_cpu')
ax_t.set_ylabel('Temperature')
ax_c.set_ylabel('Average CPU')
ax_t.set_xlabel('Period (UTC), 30-minute buckets')
ax_t.set_title('Average and last temperature, average CPU by 30-minute windows')
style_time_axis(ax_t)
ax_t.legend(handles=[l1, l2, l3], loc='upper left', frameon=False, ncol=2)
fig.tight_layout()
fig.savefig(OUT / '04-avg-last-temp-cpu-30m.png', bbox_inches='tight')
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), gridspec_kw={'width_ratios': [1, 1.35]})
axm, axc = axes
bars = axm.bar(['dimensions', 'chunks', 'compression\nenabled'], [1, 1, 1],
               color=[META, META, '#1F6F5B'], edgecolor='#2C3338', linewidth=0.6)
axm.set_ylim(0, 1.8)
axm.set_title('Hypertable: sensor_data')
axm.set_ylabel('Value')
axm.grid(True, axis='y')
for b, label in zip(bars, ['1', '1', 'true']):
    axm.text(b.get_x()+b.get_width()/2, b.get_height() + 0.08, label, ha='center', fontsize=10)

start = parse_ts('2026-10-08 00:00:00+00')
end = parse_ts('2026-10-15 00:00:00+00')
data_start = parse_ts('2026-10-12 21:33:54+00')
data_end = parse_ts('2026-10-13 21:33:54+00')
start_n = mdates.date2num(start)
end_n = mdates.date2num(end)
ds_n = mdates.date2num(data_start)
de_n = mdates.date2num(data_end)
axc.barh(1.0, end_n - start_n, left=start_n, height=0.5, color='#A8C0BF', edgecolor='#2C3338', label='chunk range')
axc.barh(0.35, de_n - ds_n, left=ds_n, height=0.35, color=TEMP, edgecolor='#2C3338', label='loaded data')
axc.set_ylim(0, 1.7)
axc.set_yticks([0.35, 1.0])
axc.set_yticklabels(['data span', '_hyper_1_1_chunk'])
axc.xaxis_date()
axc.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
axc.set_title('Chunk timeline (uncompressed)')
axc.legend(loc='upper right', frameon=False, fontsize=9)
axc.grid(True, axis='x')
fig.suptitle('Query metadata', fontsize=13, fontweight='bold', y=1.02)
fig.tight_layout()
fig.savefig(OUT / '05-metadata.png', bbox_inches='tight')
plt.close(fig)

for f in sorted(OUT.glob('*.png')):
    print(f'{f.name} ({f.stat().st_size} bytes)')
