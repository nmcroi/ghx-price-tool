import pandas as pd
import numpy as np
import itertools
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import io
import base64

# Functies voor prijsberekeningen
def calculate_costs(orders, start_bundles, prepaid_bundles, overage_cost):
    """
    Berekent de optimale combinatie van bundels voor een gegeven aantal orders.
    
    Parameters:
    - orders: Totaal aantal orders
    - start_bundles: Lijst van starter bundels (cost, orders, type)
    - prepaid_bundles: Lijst van prepaid bundels (cost, orders, type)
    - overage_cost: Kosten per order voor overage
    
    Returns:
    - min_total_cost: Minimum totale kosten
    - best_combination: Beste combinatie details
    """
    min_total_cost = float('inf')
    best_combination = None
    
    # Loop door alle starter bundels
    for starter_cost, starter_orders, starter_type in start_bundles:
        initial_bundle_cost = starter_cost
        initial_bundle_orders = starter_orders
        
        remaining_orders = max(0, orders - initial_bundle_orders)
        
        # Bereken hoeveel prepaid bundels maximaal nodig zouden zijn
        max_prepaid_bundles = (remaining_orders // min(bundle[1] for bundle in prepaid_bundles if bundle[1] > 0)) + 2
        
        # Beperk het aantal (voor performance)
        max_prepaid_bundles = min(max_prepaid_bundles, 20)
        
        # Loop door alle mogelijke aantallen prepaid bundels
        for num_prepaids in range(max_prepaid_bundles + 1):
            # Genereer combinaties met herhaling
            for bundle_combo in itertools.combinations_with_replacement(prepaid_bundles, num_prepaids):
                total_bundle_cost = sum(bundle_cost for bundle_cost, bundle_orders, bundle_type in bundle_combo)
                total_bundle_orders = sum(bundle_orders for bundle_cost, bundle_orders, bundle_type in bundle_combo)
                
                remaining_orders_after_bundles = remaining_orders - total_bundle_orders
                
                if remaining_orders_after_bundles > 0:
                    overage_cost_total = remaining_orders_after_bundles * overage_cost
                else:
                    overage_cost_total = 0
                    remaining_orders_after_bundles = 0
                
                total_cost = initial_bundle_cost + total_bundle_cost + overage_cost_total
                
                if total_cost < min_total_cost:
                    min_total_cost = total_cost
                    best_combination = (starter_cost, starter_orders, starter_type, bundle_combo, remaining_orders_after_bundles, overage_cost_total)
    
    return min_total_cost, best_combination

def bundle_description(bundle_combo):
    """Genereert een beschrijving voor bundel combinaties"""
    bundle_counts = {}
    for bundle_cost, bundle_orders, bundle_type in bundle_combo:
        if (bundle_cost, bundle_orders) in bundle_counts:
            bundle_counts[(bundle_cost, bundle_orders)] += 1
        else:
            bundle_counts[(bundle_cost, bundle_orders)] = 1
    
    descriptions = []
    for (bundle_cost, bundle_orders), count in bundle_counts.items():
        if count > 1:
            descriptions.append(f"{count}x (€{bundle_cost} voor {bundle_orders} orders)")
        else:
            descriptions.append(f"€{bundle_cost} voor {bundle_orders} orders")
    
    return ", ".join(descriptions) if descriptions else "Geen"

def display_costs_df(orders, start_bundles, prepaid_bundles, overage_cost):
    """Genereert een DataFrame met de kostenberekeningen"""
    try:
        total_cost, (starter_cost, starter_orders, starter_type, bundle_combo, remaining_orders_after_bundles, overage_cost_total) = calculate_costs(
            orders, start_bundles, prepaid_bundles, overage_cost
        )
        
        small_bundles_count = sum(1 for bundle_cost, bundle_orders, bundle_type in bundle_combo if bundle_type == 'small')
        big_bundles_count = sum(1 for bundle_cost, bundle_orders, bundle_type in bundle_combo if bundle_type == 'big')
        
        small_bundle_descriptions = bundle_description([bundle for bundle in bundle_combo if bundle[2] == 'small'])
        big_bundle_descriptions = bundle_description([bundle for bundle in bundle_combo if bundle[2] == 'big'])
        
        used_starter_bundles = {
            'small': False,
            'big': False
        }
        if starter_type == 'small':
            used_starter_bundles['small'] = True
        elif starter_type == 'big':
            used_starter_bundles['big'] = True

        small_starter_description = f"€{starter_cost} voor {starter_orders} orders" if used_starter_bundles['small'] else "Niet gebruikt"
        big_starter_description = f"€{starter_cost} voor {starter_orders} orders" if used_starter_bundles['big'] else "Niet gebruikt"
        
        overage_cost_str = f"€{overage_cost_total:.2f} voor {remaining_orders_after_bundles} extra orders" if remaining_orders_after_bundles != 0 else f"€{overage_cost_total:.0f} voor {remaining_orders_after_bundles} extra orders"
        
        data = {
            'Beschrijving': [
                'Totaal Orders',
                'Small Start Kosten',
                'Big Start Kosten',
                'Small Prepaid Aantal',
                'Big Prepaid Aantal',
                'Small Prepaid Kosten',
                'Big Prepaid Kosten',
                'Overage Orders',
                'Overage Kosten',
                'Totale Kosten'
            ],
            'Waarde': [
                orders,
                small_starter_description,
                big_starter_description,
                small_bundles_count,
                big_bundles_count,
                small_bundle_descriptions,
                big_bundle_descriptions,
                remaining_orders_after_bundles,
                overage_cost_str,
                f"€{total_cost:.2f}"
            ]
        }
        
        df = pd.DataFrame(data)
        
        # Extra informatie om terug te geven voor visualisaties
        cost_breakdown = {
            'Start Bundel': starter_cost,
            'Prepaid Bundels': sum(bundle_cost for bundle_cost, bundle_orders, bundle_type in bundle_combo),
            'Overage Kosten': overage_cost_total
        }
        
        orders_breakdown = {
            'Start Bundel': starter_orders,
            'Prepaid Bundels': sum(bundle_orders for bundle_cost, bundle_orders, bundle_type in bundle_combo),
            'Overage Orders': remaining_orders_after_bundles
        }
        
        return df, total_cost, cost_breakdown, orders_breakdown
    except Exception as e:
        print(f"Error in calculation: {e}")
        return pd.DataFrame(), 0, {}, {}

def generate_cost_comparison_chart(orders_range, start_bundles, prepaid_bundles, overage_cost):
    """Genereert een interactieve Plotly grafiek voor kostenvergelijking over orderaantallen"""
    costs = []
    for order in orders_range:
        total_cost, _ = calculate_costs(order, start_bundles, prepaid_bundles, overage_cost)
        costs.append(total_cost)
    
    fig = px.line(
        x=orders_range, 
        y=costs, 
        markers=True,
        labels={"x": "Aantal Orders", "y": "Totale Kosten (€)"},
        title='Kostenverloop per Orderaantal'
    )
    
    fig.update_traces(
        line=dict(color='#1E88E5', width=3),
        marker=dict(size=8, color='#1E88E5')
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Segoe UI, Arial", size=14),
        title=dict(font=dict(size=18, color="#1E88E5")),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="white", font_size=14),
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f2f6',
            tickfont=dict(size=12),
            title=dict(font=dict(size=14)),
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f2f6',
            tickfont=dict(size=12),
            title=dict(font=dict(size=14)),
            zeroline=False
        )
    )
    
    # Voeg een bereikbaar punt toe
    fig.add_annotation(
        x=orders_range[len(orders_range) // 2],
        y=costs[len(costs) // 2],
        text=f"€{costs[len(costs) // 2]:.2f} bij {orders_range[len(orders_range) // 2]} orders",
        showarrow=True,
        arrowhead=3,
        arrowsize=1.5,
        arrowwidth=2,
        arrowcolor="#1E88E5",
        font=dict(size=14, color="#1E88E5"),
        bgcolor="white",
        bordercolor="#1E88E5",
        borderwidth=2,
        borderpad=4,
        ax=0,
        ay=-40
    )
    
    return fig

def generate_cost_breakdown_chart(cost_breakdown):
    """Genereert een taartdiagram voor kosten breakdown"""
    labels = list(cost_breakdown.keys())
    values = list(cost_breakdown.values())
    
    # Verwijder categorieën met waarde 0
    cleaned_labels = []
    cleaned_values = []
    for i, value in enumerate(values):
        if value > 0:
            cleaned_labels.append(labels[i])
            cleaned_values.append(value)
    
    fig = px.pie(
        names=cleaned_labels,
        values=cleaned_values,
        title="Kostenverdeling",
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    
    fig.update_layout(
        font=dict(family="Segoe UI, Arial", size=14),
        title=dict(font=dict(size=18, color="#1E88E5")),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        marker=dict(line=dict(color='white', width=2)),
        pull=[0.05 if i == cleaned_values.index(max(cleaned_values)) else 0 for i in range(len(cleaned_values))]
    )
    
    return fig

def generate_orders_breakdown_chart(orders_breakdown):
    """Genereert een taartdiagram voor orders breakdown"""
    labels = list(orders_breakdown.keys())
    values = list(orders_breakdown.values())
    
    # Verwijder categorieën met waarde 0
    cleaned_labels = []
    cleaned_values = []
    for i, value in enumerate(values):
        if value > 0:
            cleaned_labels.append(labels[i])
            cleaned_values.append(value)
    
    fig = px.pie(
        names=cleaned_labels,
        values=cleaned_values,
        title="Ordersverdeling",
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Greens_r
    )
    
    fig.update_layout(
        font=dict(family="Segoe UI, Arial", size=14),
        title=dict(font=dict(size=18, color="#1E88E5")),
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        marker=dict(line=dict(color='white', width=2)),
        pull=[0.05 if i == cleaned_values.index(max(cleaned_values)) else 0 for i in range(len(cleaned_values))]
    )
    
    return fig

def generate_excel_download_link(df, filename="price_calculation.xlsx"):
    """Genereert een link om de dataframe als een excel bestand te downloaden"""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Berekening')
    
    # Maak de worksheet en workbook objecten
    workbook = writer.book
    worksheet = writer.sheets['Berekening']
    
    # Formaat de header
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        'valign': 'top',
        'fg_color': '#1E88E5',
        'font_color': 'white',
        'border': 1
    })
    
    # Formaat voor celinhoud
    cell_format = workbook.add_format({
        'border': 1,
        'valign': 'top'
    })
    
    # Pas breedte en opmaak toe
    worksheet.set_column('A:A', 20)
    worksheet.set_column('B:B', 30)
    
    # Voeg header toe
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)
    
    # Voeg cellen toe met opmaak
    for row_num in range(len(df)):
        for col_num in range(len(df.columns)):
            worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num], cell_format)
    
    writer.close()
    output.seek(0)
    
    excel_data = output.read()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="download-button">Download Excel bestand</a>'
    return href

def process_uploaded_file(uploaded_file):
    """Verwerkt een geüpload bestand en geeft een pandas DataFrame terug"""
    if uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
        return pd.read_excel(uploaded_file)
    elif uploaded_file.name.endswith('.csv'):
        return pd.read_csv(uploaded_file)
    else:
        print("Bestandsformaat niet ondersteund. Upload een Excel of CSV bestand.")
        return None

def save_scenario(name, orders, small_start_cost, small_start_orders, 
                 big_start_cost, big_start_orders, small_prepaid_cost, 
                 small_prepaid_orders, big_prepaid_cost, big_prepaid_orders,
                 overage_cost):
    """Slaat een scenario op als dictionary"""
    return {
        'name': name,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'parameters': {
            'orders': orders,
            'small_start_cost': small_start_cost,
            'small_start_orders': small_start_orders,
            'big_start_cost': big_start_cost,
            'big_start_orders': big_start_orders,
            'small_prepaid_cost': small_prepaid_cost,
            'small_prepaid_orders': small_prepaid_orders,
            'big_prepaid_cost': big_prepaid_cost,
            'big_prepaid_orders': big_prepaid_orders,
            'overage_cost': overage_cost
        }
    }

def load_scenario(scenario):
    """Laadt een scenario dictionary terug naar parameters"""
    return scenario['parameters']

def calculate_marginal_cost(orders, start_bundles, prepaid_bundles, overage_cost, step=100):
    """Berekent marginale kosten voor verschillende ordervolumes"""
    results = []
    
    for order in range(step, orders + step, step):
        cost_at_order, _ = calculate_costs(order, start_bundles, prepaid_bundles, overage_cost)
        cost_at_prev_order, _ = calculate_costs(order - step, start_bundles, prepaid_bundles, overage_cost)
        
        marginal_cost = cost_at_order - cost_at_prev_order
        marginal_cost_per_order = marginal_cost / step
        
        results.append({
            'Orders': order,
            'Marginale Kosten per Order': marginal_cost_per_order,
            'Marginale Kosten voor Stap': marginal_cost,
            'Totale Kosten': cost_at_order
        })
    
    return pd.DataFrame(results)
