import sys
import os
import time
import asyncio
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import box

# Import modules (Using the venv context)
sys.path.append(os.getcwd())

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_header():
    clear_screen()
    console.print(Panel.fit(
        "[bold cyan]KALSHI BY CEMINI[/bold cyan]\n[dim]Automated Prediction & Arbitrage Engine[/dim]",
        border_style="cyan",
        box=box.ROUNDED
    ))

def start_server():
    console.print("[green][*] Starting FastAPI Server (Backend + Dashboard)...[/green]")
    # Ensure PYTHONPATH is set so uvicorn can find 'app'
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    # Use the absolute path to uvicorn in the venv
    uvicorn_path = os.path.join(os.getcwd(), "venv", "bin", "uvicorn")
    if not os.path.exists(uvicorn_path):
        uvicorn_path = "uvicorn" # Fallback to system path if venv not found

    subprocess.run([uvicorn_path, "app.main:app", "--host", "127.0.0.1", "--port", "8000"])

def run_weather_diagnostic():
    from modules.weather_alpha.analyzer import WeatherAnalyzer
    console.print("[yellow][*] Running Weather Alpha Diagnostic...[/yellow]")
    
    analyzer = WeatherAnalyzer()
    res = asyncio.run(analyzer.analyze_market("MIA"))
    
    table = Table(title="Weather Analysis (MIA)")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")
    
    if res.get('analysis'):
        table.add_row("Consensus Temp", str(res['analysis']['consensus_temp']) + "°F")
        table.add_row("Model Variance", str(res['analysis']['variance']))
    
    console.print(table)
    
    if res.get('opportunities'):
        for op in res['opportunities']:
            console.print(f"[bold green]>> OPPORTUNITY: {op['signal']} | {op['bracket']}[/bold green]")
    else:
        console.print("[dim]No arbitrage opportunities found currently.[/dim]")
    
    Prompt.ask("\n[cyan]Press Enter to return[/cyan]")

def run_musk_diagnostic():
    from modules.musk_monitor.predictor import MuskPredictor
    console.print("[purple][*] Running Musk Personality Matrix...[/purple]")
    
    predictor = MuskPredictor()
    res = asyncio.run(predictor.predict_today())
    
    table = Table(title="Elon Behavioral Profile")
    table.add_column("Metric", style="magenta")
    table.add_column("Status", style="white")
    
    table.add_row("Predicted Volume", res['prediction']['total_daily_tweets'])
    table.add_row("Current Bio-State", res['prediction']['current_status'])
    table.add_row("Velocity (Tweets/Hr)", str(res['prediction']['velocity_per_hour']))
    
    console.print(table)
    console.print(f"[dim]News Impact: {res['factors']['news_volatility']}[/dim]")
    
    Prompt.ask("\n[cyan]Press Enter to return[/cyan]")

def run_btc_diagnostic():
    from modules.satoshi_vision.analyzer import SatoshiAnalyzer
    console.print("[orange1][*] SELECT MARKET HORIZON[/orange1]")
    console.print("[1] Scalp (15m - 1h Markets)")
    console.print("[2] Swing (Daily/Weekly Markets)")
    console.print("[3] Macro (Yearly Forecasts)")
    
    choice = Prompt.ask("Select Strategy", choices=["1", "2", "3"])
    horizon_map = {"1": "SCALP", "2": "SWING", "3": "MACRO"}
    
    console.print(f"[dim]Running {horizon_map[choice]} Analysis on BTC...[/dim]")
    
    analyzer = SatoshiAnalyzer()
    res = asyncio.run(analyzer.analyze_multiframe(asset="BTC", horizon=horizon_map[choice]))
    
    if res.get('status') == 'error':
        console.print(f"[red]Error: {res['msg']}[/red]")
    else:
        table = Table(title=f"BTC Analysis ({res['horizon']})")
        table.add_column("Metric", style="orange1")
        table.add_column("Value", style="white")
        
        sentiment_color = "green" if "BULL" in res['sentiment'] else "red" if "BEAR" in res['sentiment'] else "yellow"
        
        table.add_row("Price", f"${res['price']['current']:,}")
        table.add_row("Volatility (ATR)", f"${res['price']['atr_volatility']:,}")
        table.add_row("Sentiment", f"[bold {sentiment_color}]{res['sentiment']}[/bold]")
        table.add_row("Score", res['score'])
        
        console.print(table)
        
        # Trade Setup Panel
        setup = res['trade_setup']
        setup_color = "green" if "LONG" in setup['action'] else "red" if "SHORT" in setup['action'] else "yellow"
        
        console.print(Panel(
            f"[bold {setup_color}]ACTION: {setup['action']}[/bold {setup_color}]\n"
            f"STOP LOSS: ${setup['stop_loss']:,} (Dynamic 2x ATR)\n"
            f"TAKE PROFIT: ${setup['take_profit']:,} (Dynamic 3x ATR)\n"
            f"RISK/REWARD: {setup['risk_reward']}",
            title="--- TRADE PLAN ---",
            border_style=setup_color
        ))
        
        console.print("\n[bold]Logic Stack:[/bold]")
        for reason in res['logic']:
            console.print(f"- {reason}")
    
    Prompt.ask("\n[cyan]Press Enter to return[/cyan]")

def main_menu():
    while True:
        show_header()
        
        console.print("[1] [bold green]Start Full System[/bold green] (Server + Dashboard)")
        console.print("[2] [blue]Run Weather Diagnostic[/blue] (Module 1)")
        console.print("[3] [magenta]Run Musk Predictor[/magenta] (Module 2)")
        console.print("[4] [orange1]Run BTC Scanner[/orange1] (Module 3)")
        console.print("[5] [bold magenta]Run Social Alpha Scanner[/bold magenta] (Module 5)")
        console.print("[6] [cyan]Run Powell Protocol[/cyan] (Module 4)")
        console.print("[7] [red]Exit[/red]")
        
        choice = Prompt.ask("\n[bold]Select Option[/bold]", choices=["1", "2", "3", "4", "5", "6", "7"])
        
        if choice == "1":
            start_server()
        elif choice == "2":
            run_weather_diagnostic()
        elif choice == "3":
            run_musk_diagnostic()
        elif choice == "4":
            run_btc_diagnostic()
        elif choice == "5":
            run_social_diagnostic()
        elif choice == "6":
            run_powell_diagnostic()
        elif choice == "7":
            console.print("[red]Shutting down.[/red]")
            sys.exit()

def run_social_diagnostic():
    from modules.social_alpha.analyzer import SocialAnalyzer
    console.print("[bold magenta][*] Scanning High-Value Trader Feeds...[/bold magenta]")
    
    analyzer = SocialAnalyzer()
    res = asyncio.run(analyzer.get_target_sentiment())
    
    table = Table(title="Social Alpha Signal Matrix")
    table.add_column("Trader", style="cyan")
    table.add_column("Verdict", style="white")
    table.add_column("Polarity", style="white")
    
    for signal in res['signals']:
        color = "green" if signal['verdict'] == "BULLISH" else "red" if signal['verdict'] == "BEARISH" else "yellow"
        table.add_row(signal['trader'], f"[{color}]{signal['verdict']}[/{color}]", str(signal['polarity']))
    
    console.print(table)
    
    sentiment_color = "green" if res['aggregate_sentiment'] == "BULLISH" else "red"
    console.print(Panel(
        f"AGGREGATE SENTIMENT: [bold {sentiment_color}]{res['aggregate_sentiment']}[/bold {sentiment_color}]\n"
        f"Targets: {', '.join(res['traders_monitored'])}",
        title="--- SOCIAL ALPHA VERDICT ---",
        border_style=sentiment_color
    ))
    
    Prompt.ask("\n[cyan]Press Enter to return[/cyan]")

def run_powell_diagnostic():
    from modules.powell_protocol.analyzer import PowellAnalyzer
    console.print("[cyan][*] Running The Powell Protocol...[/cyan]")
    
    analyzer = PowellAnalyzer()
    res = asyncio.run(analyzer.analyze_fed_market())
    
    table = Table(title="Fed Interest Rate Probabilities")
    table.add_column("Outcome", style="cyan")
    table.add_column("Institutional Prob", style="white")
    table.add_column("Kalshi Price", style="white")
    
    for bracket, prob in res['consensus'].items():
        market_price = res['market_view'].get(bracket, 0)
        table.add_row(bracket, f"{prob*100}%", f"${market_price:.2f}")
    
    console.print(table)
    console.print(f"\n[bold]Regime Context:[/bold] {res['regime']}")
    
    if res['opportunities']:
        for op in res['opportunities']:
            color = "green" if "ALPHA" in op['signal'] else "red"
            console.print(Panel(
                f"[bold {color}]SIGNAL: {op['signal']}[/bold {color}]\n"
                f"Bracket: {op['bracket']}\n"
                f"Expected Value: {op['expected_value']}",
                title="--- MACRO OPPORTUNITY ---",
                border_style=color
            ))
    else:
        console.print("[dim]No significant macro arbitrage found.[/dim]")
    
    Prompt.ask("\n[cyan]Press Enter to return[/cyan]")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        start_server()
    else:
        main_menu()
