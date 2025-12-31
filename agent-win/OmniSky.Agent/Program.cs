using System;
using System.Diagnostics;
using System.Drawing;
using System.Net.Http;
using System.Threading;
using System.Windows.Forms;

namespace OmniSky.Agent
{
    static class Program
    {
        private static NotifyIcon trayIcon;
        private static ContextMenuStrip menu;
        private static readonly HttpClient http = new HttpClient { BaseAddress = new Uri("http://127.0.0.1:8000") };
        private static readonly string[] HeavyProcesses = { "GTA5", "Cyberpunk2077", "RDR2", "blender", "premiere" };
        private static bool isPaused = false;
        private static System.Threading.Timer monitorTimer;

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            // Create Tray Icon
            trayIcon = new NotifyIcon
            {
                Icon = SystemIcons.Application, // Use built-in icon
                Text = "OmniSky Agent",
                Visible = true
            };

            // Create Menu
            menu = new ContextMenuStrip();
            menu.Items.Add("▶️ Resume", null, (s, e) => SendResume());
            menu.Items.Add("⏸️ Pause", null, (s, e) => SendPause());
            menu.Items.Add("-");
            menu.Items.Add("🌐 Open UI", null, (s, e) => Process.Start(new ProcessStartInfo("http://127.0.0.1:8000") { UseShellExecute = true }));
            menu.Items.Add("-");
            menu.Items.Add("❌ Exit", null, (s, e) => Application.Exit());

            trayIcon.ContextMenuStrip = menu;
            trayIcon.DoubleClick += (s, e) => Process.Start(new ProcessStartInfo("http://127.0.0.1:8000") { UseShellExecute = true });

            // Start Monitor
            monitorTimer = new System.Threading.Timer(MonitorCallback, null, 0, 3000);

            Application.Run();
            trayIcon.Dispose();
        }

        static void MonitorCallback(object state)
        {
            bool shouldPause = false;

            // Check for heavy processes
            foreach (var proc in Process.GetProcesses())
            {
                foreach (var heavy in HeavyProcesses)
                {
                    if (proc.ProcessName.IndexOf(heavy, StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        shouldPause = true;
                        break;
                    }
                }
                if (shouldPause) break;
            }

            // Check CPU (simplified)
            // For real impl, use PerformanceCounter

            if (shouldPause && !isPaused)
            {
                SendPause();
                isPaused = true;
                trayIcon.ShowBalloonTip(2000, "OmniSky", "Paused - Heavy app detected", ToolTipIcon.Info);
            }
            else if (!shouldPause && isPaused)
            {
                SendResume();
                isPaused = false;
                trayIcon.ShowBalloonTip(2000, "OmniSky", "Resumed - System free", ToolTipIcon.Info);
            }
        }

        static async void SendPause()
        {
            try { await http.PostAsync("/pause", new StringContent("{\"reason\":\"AGENT\"}", System.Text.Encoding.UTF8, "application/json")); } catch { }
        }

        static async void SendResume()
        {
            try { await http.PostAsync("/resume", null); } catch { }
        }
    }
}
