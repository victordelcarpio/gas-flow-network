
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import sys
import os

# Get folder path from command line argument or use current directory
if len(sys.argv) > 1:
    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        sys.exit(1)
    os.chdir(folder_path)
    print(f"Using folder: {folder_path}\n")
else:
    folder_path = os.getcwd()
    print(f"Using current folder: {folder_path}\n")

# Check if required files exist
required_files = ['report_pipeflow.csv', 'report_lngflow.csv']
for file in required_files:
    if not os.path.isfile(file):
        print(f"Error: '{file}' not found in {folder_path}")
        sys.exit(1)

# Define region groups
region_groups = {
    'EMEA': {
        'Germany', 'France', 'Italy', 'Spain', 'Poland', 'Austria', 'Hungary', 'Slovakia', 'Slovenia',
        'Belgium', 'Netherlands', 'United Kingdom', 'Greece', 'Turkey', 'Russia', 'Ukraine', 'Belarus',
        'Lithuania', 'Latvia', 'Estonia', 'Norway', 'Sweden', 'Finland', 'Portugal', 'Switzerland',
        'Czech Republic', 'Denmark', 'Ireland', 'Bulgaria', 'Romania', 'Serbia', 'Croatia', 'Algeria',
        'Tunisia', 'Morocco', 'Egypt', 'Libya', 'Nigeria', 'Qatar', 'Iran', 'Iraq',
        'Rest of Africa', 'Rest of Arabic Peninsula'
    },
    'NORAM': {'US', 'Canada', 'Mexico'},
    'LATAM': {
        'Argentina', 'Brazil', 'Chile', 'Colombia', 'Peru', 'Uruguay', 'Bolivia',
        'Rest of Central & South America', 'Trinidad and Tobago'
    },
    'APAC': {
        'China', 'India', 'Japan', 'Korea, Republic of', 'Indonesia', 'Malaysia', 'Singapore',
        'Taiwan', 'Philippines', 'Australia', 'Papua New Guinea & Brunei', 'Rest of Asia Pacific'
    }
}


# Ask if user wants single year analysis or comparison first
analysis_mode = None
comparison_years = None
comparison_type = None
years = None

while True:
    mode_input = input("Choose analysis mode:\n1. Single year analysis\n2. Compare two years\nEnter (1 or 2): ").strip()
    if mode_input == '1':
        analysis_mode = 'single'
        
        # Get years from user input for single year analysis
        while True:
            try:
                years_input = input("Enter year(s) to analyze (comma or space-separated, e.g., 2026, 2030, 2040, 2050): ")
                # Parse years from input
                years = []
                for y in years_input.replace(',', ' ').split():
                    y = y.strip()
                    if y:
                        year_val = int(y)
                        if 2023 <= year_val <= 2054:
                            years.append(year_val)
                        else:
                            print(f"Year {year_val} is outside valid range (2023-2054), skipping")
                
                if years:
                    years = sorted(set(years))  # Remove duplicates and sort
                    break
                else:
                    print("Please enter at least one valid year")
            except ValueError:
                print("Invalid input. Please enter valid year numbers separated by commas or spaces.")
        
        break
        
    elif mode_input == '2':
        analysis_mode = 'comparison'
        comparison_type = 'network'  # Always use network comparison
        
        # Ask which two years to compare
        while True:
            try:
                comp_input = input("Enter the two years to compare (comma-separated, e.g., 2026,2030): ")
                comp_years = [int(y.strip()) for y in comp_input.split(',')]
                
                if len(comp_years) != 2:
                    print("Please enter exactly 2 years")
                    continue
                
                if comp_years[0] == comp_years[1]:
                    print("Years must be different")
                    continue
                
                # Validate year ranges
                valid_years = all(2023 <= y <= 2054 for y in comp_years)
                if not valid_years:
                    print("All years must be in range 2023-2054")
                    continue
                
                # Sort so earlier year is first
                comparison_years = tuple(sorted(comp_years))
                years = list(comparison_years)  # Store for data loading
                break
            except ValueError:
                print("Invalid input. Please enter valid year numbers separated by commas (e.g., 2026,2030).")
        
        break
    else:
        print("Invalid choice. Please enter 1 or 2.")

if analysis_mode == 'single':
    print(f"\nMode: Single year analysis for {', '.join(map(str, years))}\n")
else:
    print(f"\nMode: Comparison between {comparison_years[0]} and {comparison_years[1]}\n")

# Ask once for region filter (applies to all modes)
region_filter = input("Enter region to filter (EMEA, NORAM, LATAM, APAC) or press Enter to show full network: ").strip().upper()
apply_region_filter = region_filter in region_groups
if apply_region_filter:
    print(f"Filtering to region: {region_filter}")
elif region_filter:
    print(f"Region '{region_filter}' not recognised. Showing full network.")

include_partners = False
if apply_region_filter:
    include_partners = input("Include trade partners outside the region? (y/N): ").strip().lower() == 'y'

region_tag = f"_{region_filter}" if apply_region_filter else ""


def save_csv(df, name):
    df.to_csv(name, index=False)
    print(f"Saved: {name}")



# Assume the CSVs include many metrics; we only want the actual flow volumes.
# In the pipeflow file the relevant ITEM is "Flow" (typically "Flow [bcm]").
# In the LNG file the data we need is the gross flow ("Flow (gross) [bcm]").
# Read raw data first.
pipe_flows = pd.read_csv('report_pipeflow.csv')
lng_flows = pd.read_csv('report_lngflow.csv')

# From here on, all outputs (charts and CSVs) are written to <data folder>\network_outputs
output_dir = os.path.join(os.getcwd(), 'network_outputs')
os.makedirs(output_dir, exist_ok=True)
os.chdir(output_dir)
print(f"Outputs will be saved to: {output_dir}\n")

# filter to the correct ITEM rows and keep only columns we actually use
if 'ITEM' in pipe_flows.columns:
    pipe_flows = pipe_flows[
        pipe_flows['ITEM'].astype(str).str.contains('flow', case=False, na=False)
        & ~pipe_flows['ITEM'].astype(str).str.contains('gross', case=False, na=False)
    ]
    pipe_flows = pipe_flows[['YEAR', 'COUNTRY_FROM', 'COUNTRY_TO', 'VALUE']]

if 'ITEM' in lng_flows.columns:
    lng_flows = lng_flows[
        lng_flows['ITEM'].astype(str).str.contains('flow', case=False, na=False)
        & lng_flows['ITEM'].astype(str).str.contains('gross', case=False, na=False)
    ]
    lng_flows = lng_flows[['YEAR', 'COUNTRY_FROM', 'COUNTRY_TO', 'VALUE']]


# Function to standardize country names
def standardize_country_name(name):
    """
    Standardize country names:
    1. Remove parenthetical suffixes (e.g., 'Poland (Yamal)' -> 'Poland')
    2. Map US regions to 'US'
    3. Map Canada regions to 'Canada'
    4. Map Interconnector Greece Bulgaria to 'Greece'
    """
    us_regions = {
        'New England', 'Mid-Atlantic', 'South Atlantic', 'East North Central',
        'East South Central', 'West South Central', 'West North Central', 'Mountain', 'Pacific', 'Texas', 'Gulf of Mexico'
    }
    
    canada_regions = {'Canada East', 'Canada West'}
    
    # Map US regions
    if name in us_regions:
        return 'US'
    
    # Map Canada regions
    if name in canada_regions:
        return 'Canada'
    
    # Map Interconnector Greece Bulgaria to Greece
    if name == 'Interconnector Greece Bulgaria':
        return 'Greece'
    
    # Remove parenthetical suffixes
    if '(' in name and ')' in name:
        name = name.split('(')[0].strip()
    
    return name

# Apply standardization to both dataframes
pipe_flows['COUNTRY_FROM'] = pipe_flows['COUNTRY_FROM'].apply(standardize_country_name)
pipe_flows['COUNTRY_TO'] = pipe_flows['COUNTRY_TO'].apply(standardize_country_name)
lng_flows['COUNTRY_FROM'] = lng_flows['COUNTRY_FROM'].apply(standardize_country_name)
lng_flows['COUNTRY_TO'] = lng_flows['COUNTRY_TO'].apply(standardize_country_name)

# Filter or aggregate data for the year of interest
# year variable is set from user input above

# Add flow type to distinguish pipeline vs LNG
pipe_flows['flow_type'] = 'pipeline'
lng_flows['flow_type'] = 'lng'



# ============ VISUALIZATION CODE ============

# Function to plot network with a specific metric


def plot_network(graph, positions, metric_dict, title, cmap='viridis'):
    """
    Visualise network with nodes coloured by metric values, styled consistently with flow change plots.
    """
    import math
    import matplotlib.pyplot as plt
    import networkx as nx

    plt.figure(figsize=(16, 12))

    # Node sizes based on degree
    node_sizes = [300 + (graph.degree(node) * 100) for node in graph.nodes()]

    # Node colours based on metric
    node_values = list(metric_dict.values())
    max_val = max(node_values) if node_values else 1
    min_val = min(node_values) if node_values else 0
    node_colours = [metric_dict.get(node, 0) for node in graph.nodes()]

    # Draw nodes
    nodes = nx.draw_networkx_nodes(
        graph, positions,
        node_size=node_sizes,
        node_color=node_colours,
        cmap=plt.get_cmap(cmap),
        alpha=0.4,
        edgecolors='black',
        linewidths=0.8,
        vmin=min_val,
        vmax=max_val
    )

    # Draw edges with consistent arrow style
    edges = [(u, v) for u, v in graph.edges() if u != v]
    weights = [graph[u][v]['weight'] for u, v in edges]
    max_weight = max(weights) if weights else 1
    widths = [2.5 * (w / max_weight) for w in weights]

    nx.draw_networkx_edges(
        graph, positions,
        width=[w * 1 for w in widths],  # increase line thickness
        edge_color='black',
        alpha=0.4,  # make more visible
        arrows=True,
        arrowsize=18,  # increase size
        arrowstyle='-|>',
        connectionstyle='arc3,rad=0.1'
    )


    # Draw labels with metric values
    labels = {
        node: f"{node}\n({metric_dict.get(node, 0):.3f})"
        for node in graph.nodes()
    }
    nx.draw_networkx_labels(graph, positions, labels, font_size=7, font_weight='bold')

    # Title and colourbar
    plt.title(title, fontsize=16, fontweight='bold')
    cbar = plt.colorbar(nodes, shrink=0.85, pad=0.02)
    cbar.set_label('Metric Value', fontsize=12)
    cbar.ax.tick_params(labelsize=10)

    plt.axis('off')
    plt.tight_layout()

    # Save figure
    filename = f"{title.replace(' ', '_').replace(':', '')}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    plt.close()


# Helper function to prevent node overlaps
def prevent_overlaps(pos, min_distance=0.25, max_iterations=150):
    """
    Adjust node positions to prevent overlaps
    min_distance: minimum distance between nodes (in normalized coordinates)
    """
    import math
    
    for iteration in range(max_iterations):
        moved = False
        nodes = list(pos.keys())
        
        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                x1, y1 = pos[node1]
                x2, y2 = pos[node2]
                
                # Calculate distance
                dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                # If nodes are too close, push them apart
                if dist < min_distance and dist > 0:
                    # Direction from node1 to node2
                    dx = (x2 - x1) / dist
                    dy = (y2 - y1) / dist
                    
                    # Push them apart with stronger force
                    push_distance = (min_distance - dist) / 2 + 0.02
                    pos[node1][0] -= dx * push_distance
                    pos[node1][1] -= dy * push_distance
                    pos[node2][0] += dx * push_distance
                    pos[node2][1] += dy * push_distance
                    
                    moved = True
        
        if not moved:
            break
    
    return pos


# Function to filter graph by region
def filter_graph_by_region(graph, region_name, region_groups, include_partners=False):
    """
    Returns a subgraph restricted to the selected region.
    By default only edges with BOTH ends in the region are kept; with include_partners=True,
    edges where either end is in the region are kept (pulls in outside trade partners).
    """
    region_nodes = region_groups.get(region_name.upper(), set())
    G_region = nx.DiGraph()

    for u, v, data in graph.edges(data=True):
        in_u, in_v = u in region_nodes, v in region_nodes
        if (in_u or in_v) if include_partners else (in_u and in_v):
            G_region.add_edge(u, v, **data)

    # Ensure all region nodes are included even if isolated
    for node in region_nodes:
        if node in graph:
            G_region.add_node(node)

    return G_region


# Function to plot change network between two years
def plot_change_network(G_year1, G_year2, pos_year1, pos_year2, year1, year2):
    """
    Visualize changes in flows between two years
    Green edges = increases, Red edges = decreases
    """
    # Merge the two graphs to get all nodes
    all_nodes = set(G_year1.nodes()) | set(G_year2.nodes())
    G_combined = nx.DiGraph()
    G_combined.add_nodes_from(all_nodes)
    
    # Calculate changes
    edge_changes = {}  # (u, v) -> change_value
    
    for u, v in list(set(G_year1.edges()) | set(G_year2.edges())):
        flow_y1 = G_year1[u][v]['weight'] if G_year1.has_edge(u, v) else 0
        flow_y2 = G_year2[u][v]['weight'] if G_year2.has_edge(u, v) else 0
        change = flow_y2 - flow_y1
        
        if abs(change) > 0.001:  # Only include meaningful changes
            edge_changes[(u, v)] = change
            G_combined.add_edge(u, v, weight=abs(change), change=change)
    
    if not edge_changes:
        print(f"No significant changes between {year1} and {year2}")
        return
    
    # Use a weighted average of both layouts with better spacing
    pos_combined = {}
    for node in all_nodes:
        pos1 = pos_year1.get(node, [0, 0])
        pos2 = pos_year2.get(node, [0, 0])
        pos_combined[node] = [(pos1[0] + pos2[0]) / 2, (pos1[1] + pos2[1]) / 2]
    
    # Re-layout the combined graph with better spacing parameters to prevent overlaps
    pos_combined = nx.spring_layout(G_combined, k=5, iterations=100, seed=42, scale=2)
    
    # Apply overlap prevention algorithm
    pos_combined = prevent_overlaps(pos_combined, min_distance=0.15, max_iterations=100)
    
    plt.figure(figsize=(16, 12))
    
    # Node colors based on net change (in/out flows)
    node_changes = {}
    for node in all_nodes:
        in_change = sum(edge_changes.get((u, node), 0) for u in all_nodes)
        out_change = sum(edge_changes.get((node, v), 0) for v in all_nodes)
        node_changes[node] = in_change + out_change
    
    node_colors = [node_changes.get(node, 0) for node in G_combined.nodes()]
    # More proportional node sizes
    node_sizes = [200 + (abs(node_changes.get(node, 0)) * 50) for node in G_combined.nodes()]
    
    # Draw nodes
    max_abs_val = max(abs(v) for v in node_colors) if node_colors else 1
    nodes = nx.draw_networkx_nodes(
        G_combined, pos_combined,
        node_size=node_sizes,
        node_color=node_colors,
        cmap=plt.cm.RdYlGn,
        alpha=0.4,
        edgecolors='black',
        linewidths=1.5,
        vmin=-max_abs_val,
        vmax=max_abs_val
    )
    
    # Filter edges to show only significant changes (top 70% by magnitude)
    edge_magnitudes = [(k, abs(v)) for k, v in edge_changes.items()]
    edge_magnitudes.sort(key=lambda x: x[1], reverse=True)
    threshold_idx = max(1, int(len(edge_magnitudes) * 0.7))
    threshold_value = edge_magnitudes[threshold_idx][1]
    
    # Draw edges with colors (green for increases, red for decreases)
    for (u, v), change in edge_changes.items():
        if abs(change) < threshold_value:
            continue  # Skip less significant edges
        
        color = 'green' if change > 0 else 'red'
        width = 2 * (abs(change) / max(abs(c) for c in edge_changes.values()))
        
        # Get node positions to calculate arrow start/end points
        x1, y1 = pos_combined[u]
        x2, y2 = pos_combined[v]
        
        # Calculate direction and shrink to avoid overlapping with node circles
        import math
        dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        if dist > 0:
            # Shrink factor to pull arrows back from node circumference (larger factor for better spacing)
            shrink_factor = 0.12
            x1_adj = x1 + (x2 - x1) * shrink_factor
            y1_adj = y1 + (y2 - y1) * shrink_factor
            x2_adj = x2 - (x2 - x1) * shrink_factor
            y2_adj = y2 - (y2 - y1) * shrink_factor
            
            # Draw arrow manually
            plt.annotate('', xy=(x2_adj, y2_adj), xytext=(x1_adj, y1_adj),
                        arrowprops=dict(arrowstyle='->', lw=width, color=color, alpha=0.6, 
                                      connectionstyle='arc3,rad=0.1'))
    
    
    # Draw labels with change values
    labels = {}
    for node in G_combined.nodes():
        change_val = node_changes.get(node, 0)
        labels[node] = f"{node}\n({change_val:+.3f})"
    
    nx.draw_networkx_labels(G_combined, pos_combined, labels, font_size=7, font_weight='bold')
    
    plt.title(f'Network Flow Changes: {year1} -> {year2} (Green=Increase, Red=Decrease)', fontsize=16, fontweight='bold')
    plt.colorbar(nodes, label='Net Change (bcm)')
    
    # Add note about Unspecified
    note_text = ('Note: "Unspecified" represents unallocated flows (trading intermediaries/portfolio players)\n'
                 'where the final destination is not explicitly tracked in the model.')
    plt.figtext(0.5, 0.02, note_text, ha='center', fontsize=9, style='italic', 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.axis('off')
    plt.tight_layout()
    filename = f'Network_Changes_{year1}_to_{year2}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Saved: {filename}")
    plt.close()
    
    # CSV outputs: edge and node changes
    edge_rows = [{
        'from': u, 'to': v,
        f'flow_{year1}_bcm': G_year1[u][v]['weight'] if G_year1.has_edge(u, v) else 0,
        f'flow_{year2}_bcm': G_year2[u][v]['weight'] if G_year2.has_edge(u, v) else 0,
        'change_bcm': c,
    } for (u, v), c in edge_changes.items()]
    save_csv(pd.DataFrame(edge_rows).sort_values('change_bcm', ascending=False),
             f'edge_changes{region_tag}_{year1}_to_{year2}.csv')

    node_rows = []
    for node in all_nodes:
        imp1 = G_year1.in_degree(node, weight='weight') if node in G_year1 else 0
        exp1 = G_year1.out_degree(node, weight='weight') if node in G_year1 else 0
        imp2 = G_year2.in_degree(node, weight='weight') if node in G_year2 else 0
        exp2 = G_year2.out_degree(node, weight='weight') if node in G_year2 else 0
        node_rows.append({
            'country': node,
            f'imports_{year1}_bcm': imp1, f'imports_{year2}_bcm': imp2, 'import_change_bcm': imp2 - imp1,
            f'exports_{year1}_bcm': exp1, f'exports_{year2}_bcm': exp2, 'export_change_bcm': exp2 - exp1,
            'net_import_change_bcm': (imp2 - exp2) - (imp1 - exp1),
            'chart_label_value': node_changes.get(node, 0),
        })
    save_csv(pd.DataFrame(node_rows).sort_values('country'),
             f'node_changes{region_tag}_{year1}_to_{year2}.csv')

    # Print summary
    print(f"\n{'='*60}")
    print(f"Flow Changes Summary ({year1} -> {year2}):")
    print(f"{'='*60}")
    
    increases = {k: v for k, v in edge_changes.items() if v > 0}
    decreases = {k: v for k, v in edge_changes.items() if v < 0}
    
    print(f"\nIncreased Routes ({len(increases)}):")
    for (u, v), change in sorted(increases.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {u} -> {v}: +{change:.2f} bcm")
    
    print(f"\nDecreased Routes ({len(decreases)}):")
    for (u, v), change in sorted(decreases.items(), key=lambda x: x[1])[:10]:
        print(f"  {u} -> {v}: {change:.2f} bcm")

# Function to plot change metrics between two years
def plot_change_metrics(G_year1, G_year2, pos_year1, pos_year2, year1, year2):
    """
    Visualize changes in node metrics between two years
    Shows import/export/net flow changes per country
    """
    all_nodes = set(G_year1.nodes()) | set(G_year2.nodes())
    
    # Calculate metrics for both years
    metrics_y1 = {}
    metrics_y2 = {}
    
    for node in all_nodes:
        in_flow_y1 = G_year1.in_degree(node, weight='weight') if node in G_year1 else 0
        out_flow_y1 = G_year1.out_degree(node, weight='weight') if node in G_year1 else 0
        
        in_flow_y2 = G_year2.in_degree(node, weight='weight') if node in G_year2 else 0
        out_flow_y2 = G_year2.out_degree(node, weight='weight') if node in G_year2 else 0
        
        metrics_y1[node] = {
            'imports': in_flow_y1,
            'exports': out_flow_y1,
            'net': in_flow_y1 - out_flow_y1
        }
        
        metrics_y2[node] = {
            'imports': in_flow_y2,
            'exports': out_flow_y2,
            'net': in_flow_y2 - out_flow_y2
        }
    
    # Calculate changes
    metric_changes = {}
    for node in all_nodes:
        metric_changes[node] = {
            'import_change': metrics_y2[node]['imports'] - metrics_y1[node]['imports'],
            'export_change': metrics_y2[node]['exports'] - metrics_y1[node]['exports'],
            'net_change': metrics_y2[node]['net'] - metrics_y1[node]['net']
        }
    
    # Use average position
    pos_combined = {}
    for node in all_nodes:
        pos1 = pos_year1.get(node, [0, 0])
        pos2 = pos_year2.get(node, [0, 0])
        pos_combined[node] = [(pos1[0] + pos2[0]) / 2, (pos1[1] + pos2[1]) / 2]
    
    # Create visualizations for each metric
    for metric_name in ['import_change', 'export_change', 'net_change']:
        plt.figure(figsize=(16, 12))
        
        metric_values = [metric_changes[node][metric_name] for node in all_nodes]
        max_abs_val = max(abs(v) for v in metric_values) if metric_values else 1
        
        node_colors = [metric_changes[node][metric_name] for node in all_nodes]
        
        # Create a dummy graph just for visualization
        G_dummy = nx.DiGraph()
        G_dummy.add_nodes_from(all_nodes)
        
        nodes = nx.draw_networkx_nodes(
            G_dummy, pos_combined,
            node_size=500,
            node_color=node_colors,
            cmap=plt.cm.RdYlGn,
            alpha=0.4,
            edgecolors='black',
            linewidths=1.5,
            vmin=-max_abs_val,
            vmax=max_abs_val
        )
        
        # Draw labels
        labels = {}
        for node in all_nodes:
            change_val = metric_changes[node][metric_name]
            labels[node] = f"{node}\n({change_val:+.2f})"
        
        nx.draw_networkx_labels(G_dummy, pos_combined, labels, font_size=7, font_weight='bold')
        
        metric_display = metric_name.replace('_', ' ').title()
        plt.title(f'Network: {metric_display} ({year1} -> {year2})', fontsize=16, fontweight='bold')
        plt.colorbar(nodes, label=f'{metric_display} (bcm)')
        plt.axis('off')
        plt.tight_layout()
        filename = f'Network_Change_{metric_display.replace(" ", "_")}_{year1}_to_{year2}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved: {filename}")
        plt.close()
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Metric Changes Summary ({year1} -> {year2}):")
    print(f"{'='*60}")
    
    print(f"\nTop Import Increases:")
    sorted_imports = sorted(metric_changes.items(), key=lambda x: x[1]['import_change'], reverse=True)[:5]
    for node, changes in sorted_imports:
        if changes['import_change'] > 0:
            print(f"  {node}: +{changes['import_change']:.2f} bcm")
    
    print(f"\nTop Export Increases:")
    sorted_exports = sorted(metric_changes.items(), key=lambda x: x[1]['export_change'], reverse=True)[:5]
    for node, changes in sorted_exports:
        if changes['export_change'] > 0:
            print(f"  {node}: +{changes['export_change']:.2f} bcm")

# Generate visualizations for all selected years
print("\nGenerating network visualizations...")

if analysis_mode == 'single':
    # Single year analysis
    for year in years:
        # Filter and prepare data for this year
        flows_year = pd.concat([
            pipe_flows[pipe_flows.YEAR == year],
            lng_flows[lng_flows.YEAR == year]
        ])
        
        flows_year_agg = flows_year.groupby(['COUNTRY_FROM','COUNTRY_TO'], as_index=False).agg({
            'VALUE': 'sum',
            'flow_type': lambda x: list(set(x))
        })
        
        # Filter out zero or negligible flows (only keep connections with actual flows)
        flows_year_agg = flows_year_agg[flows_year_agg['VALUE'] > 0.001]
        
        # Build directed graph for this year
        G_year = nx.DiGraph()
        for _, row in flows_year_agg.iterrows():
            src = row['COUNTRY_FROM']
            dst = row['COUNTRY_TO']

            if src == dst:
                continue  # ✅ Skip self-loops after standardisation

            vol = row['VALUE']
            flow_types = row['flow_type']
            
            if G_year.has_edge(src, dst):
                G_year[src][dst]['weight'] += vol
                for ft in flow_types:
                    if ft not in G_year[src][dst]['types']:
                        G_year[src][dst]['types'].append(ft)
            else:
                G_year.add_edge(src, dst, weight=vol, types=flow_types)
        
        # Apply region filter if selected
        if apply_region_filter:
            G_filtered = filter_graph_by_region(G_year, region_filter, region_groups, include_partners)
        else:
            G_filtered = G_year

        if G_filtered.number_of_nodes() == 0:
            print(f"No flows found for {year} with the selected filter, skipping.")
            continue

         # Compute metrics
        deg_cent_year = nx.degree_centrality(G_filtered)
        btw_cent_year = nx.betweenness_centrality(G_filtered, weight=None)
        pr_cent_year = nx.pagerank(G_filtered, weight='weight')
        
        undirected_G_year = G_filtered.to_undirected()
        clust_year = nx.clustering(undirected_G_year)
        
        import networkx.algorithms.community as nx_comm
        communities_year = nx_comm.greedy_modularity_communities(undirected_G_year, weight='weight')
        modularity_value_year = nx_comm.modularity(undirected_G_year, communities_year, weight='weight')
        
        # Layout for this year
        pos_year = nx.spring_layout(G_filtered, k=2, iterations=100, seed=42)
        pos_year = prevent_overlaps(pos_year, min_distance=0.15, max_iterations=100)

        # Generate visualizations for this year
        plot_network(G_filtered, pos_year, deg_cent_year, f'Network: Degree Centrality ({year})', cmap='Blues')
        plot_network(G_filtered, pos_year, btw_cent_year, f'Network: Betweenness Centrality ({year})', cmap='Reds')
        plot_network(G_filtered, pos_year, pr_cent_year, f'Network: PageRank ({year})', cmap='Greens')
        plot_network(G_filtered, pos_year, clust_year, f'Network: Clustering Coefficient ({year})', cmap='Oranges')
        
        # Community visualization
        plt.figure(figsize=(16, 12))
        
        community_colors = {}
        colors = plt.cm.Set3(range(len(communities_year)))
        for idx, community in enumerate(communities_year):
            for node in community:
                community_colors[node] = colors[idx]
        
        node_colors_list = [community_colors.get(node, [0, 0, 0, 1]) for node in G_filtered.nodes()]
        node_sizes = [300 + (G_filtered.degree(node) * 100) for node in G_filtered.nodes()]
        
        nx.draw_networkx_nodes(
            G_filtered, pos_year,
            node_size=node_sizes,
            node_color=node_colors_list,
            alpha=0.4,
            edgecolors='black',
            linewidths=1.5
        )

        edges = G_filtered.edges()
        weights = [G_filtered[u][v]['weight'] for u, v in edges]
        max_weight = max(weights) if weights else 1
        widths = [3 * (w / max_weight) for w in weights]
        
        nx.draw_networkx_edges(
            G_filtered, pos_year,
            width=widths,
            alpha=0.4,
            arrows=True,
            arrowsize=18,
            arrowstyle='-|>',
            connectionstyle='arc3,rad=0.1'
        )

        nx.draw_networkx_labels(G_filtered, pos_year, font_size=7, font_weight='bold')
        
        plt.title(f'Network: Communities - Modularity: {modularity_value_year:.3f} ({year})', fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        filename = f'Network_Communities_{year}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Saved: {filename}")
        plt.close()
        
        # ---- CSV outputs: node metrics and edge flows ----
        node_community = {n: idx + 1 for idx, c in enumerate(communities_year) for n in c}
        node_rows = [{
            'year': year,
            'country': n,
            'degree_centrality': deg_cent_year[n],
            'betweenness_centrality': btw_cent_year[n],
            'pagerank': pr_cent_year[n],
            'clustering_coefficient': clust_year[n],
            'community': node_community.get(n),
            'imports_bcm': G_filtered.in_degree(n, weight='weight'),
            'exports_bcm': G_filtered.out_degree(n, weight='weight'),
            'net_imports_bcm': G_filtered.in_degree(n, weight='weight') - G_filtered.out_degree(n, weight='weight'),
        } for n in G_filtered.nodes()]
        save_csv(pd.DataFrame(node_rows), f'node_metrics{region_tag}_{year}.csv')

        edge_rows = [{
            'year': year,
            'from': u,
            'to': v,
            'flow_bcm': d['weight'],
            'flow_types': ', '.join(sorted(d.get('types', []))),
        } for u, v, d in G_filtered.edges(data=True)]
        save_csv(pd.DataFrame(edge_rows, columns=['year', 'from', 'to', 'flow_bcm', 'flow_types']),
                 f'edge_flows{region_tag}_{year}.csv')
        community_rows = []

        print(f"\n{'='*60}")
        print(f"Community Detection Results for {year} (Modularity: {modularity_value_year:.3f}):")
        print(f"{'='*60}")
        for idx, community in enumerate(communities_year):
            print(f"\nCommunity {idx + 1}: {community}")
            
            internal_flow = 0
            external_flow = 0
            internal_types = set()
            external_types = set()
            
            for u, v in G_filtered.edges():
                weight = G_filtered[u][v]['weight']
                edge_types = G_filtered[u][v]['types']
                
                if u in community and v in community:
                    internal_flow += weight
                    internal_types.update(edge_types)
                elif (u in community) or (v in community):
                    external_flow += weight
                    external_types.update(edge_types)
            
            in_degree = sum(G_filtered.in_degree(node, weight='weight') for node in community)
            out_degree = sum(G_filtered.out_degree(node, weight='weight') for node in community)
            
            total_flow = internal_flow + external_flow
            internal_pct = (internal_flow / total_flow * 100) if total_flow > 0 else 0
            
            internal_mode = ', '.join(sorted(internal_types)) if internal_types else 'None'
            external_mode = ', '.join(sorted(external_types)) if external_types else 'None'
            primary_mode = internal_mode if internal_types else external_mode
            
            print(f"  Size: {len(community)} nodes")
            print(f"  Internal flow: {internal_flow:.2f} bcm ({internal_pct:.1f}%) - via {internal_mode}")
            print(f"  External flow: {external_flow:.2f} bcm ({100-internal_pct:.1f}%) - via {external_mode}")
            print(f"  Net imports: {in_degree - out_degree:.2f} bcm")
            print(f"  Primary unification: {primary_mode.upper()} transport")
            
            community_nodes = list(community)
            node_flows = {node: G_filtered.in_degree(node, weight='weight') + G_filtered.out_degree(node, weight='weight')
                          for node in community_nodes}
            top_nodes = sorted(node_flows.items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"  Key nodes: {', '.join([f'{n[0]} ({n[1]:.1f} bcm)' for n in top_nodes])}")

            community_rows.append({
                'year': year,
                'community': idx + 1,
                'modularity': modularity_value_year,
                'size': len(community),
                'members': '; '.join(sorted(community)),
                'internal_flow_bcm': internal_flow,
                'external_flow_bcm': external_flow,
                'internal_pct': internal_pct,
                'net_imports_bcm': in_degree - out_degree,
                'primary_transport': primary_mode,
                'key_nodes': '; '.join(f'{n[0]} ({n[1]:.1f} bcm)' for n in top_nodes),
            })
        save_csv(pd.DataFrame(community_rows), f'communities{region_tag}_{year}.csv')

    print("Visualizations saved!")

else:
    # Comparison mode: analyze two years and show changes
    year1, year2 = comparison_years
    
    # Build graphs for both years
    graphs = {}
    positions = {}
    
    for year in comparison_years:
        flows_year = pd.concat([
            pipe_flows[pipe_flows.YEAR == year],
            lng_flows[lng_flows.YEAR == year]
        ])
        
        flows_year_agg = flows_year.groupby(['COUNTRY_FROM','COUNTRY_TO'], as_index=False).agg({
            'VALUE': 'sum',
            'flow_type': lambda x: list(set(x))
        })
        
        # Filter out zero or negligible flows
        flows_year_agg = flows_year_agg[flows_year_agg['VALUE'] > 0.001]
        
        G = nx.DiGraph()
        for _, row in flows_year_agg.iterrows():
            src = row['COUNTRY_FROM']
            dst = row['COUNTRY_TO']
            vol = row['VALUE']
            flow_types = row['flow_type']
            
            if G.has_edge(src, dst):
                G[src][dst]['weight'] += vol
                for ft in flow_types:
                    if ft not in G[src][dst]['types']:
                        G[src][dst]['types'].append(ft)
            else:
                G.add_edge(src, dst, weight=vol, types=flow_types)
        

        # Apply region filter before storing the graph and layout
        if apply_region_filter:
            G = filter_graph_by_region(G, region_filter, region_groups, include_partners)

        graphs[year] = G
        positions[year] = nx.spring_layout(G, k=2, iterations=50, seed=42)

    
    G_year1 = graphs[year1]
    G_year2 = graphs[year2]
    pos_year1 = positions[year1]
    pos_year2 = positions[year2]

    
 
    # Generate comparison visualization
    if comparison_type == 'network':
        plot_change_network(G_year1, G_year2, pos_year1, pos_year2, year1, year2)
    else:  # comparison_type == 'metrics'
        plot_change_metrics(G_year1, G_year2, pos_year1, pos_year2, year1, year2)
    
    print("Comparison visualizations saved!")
