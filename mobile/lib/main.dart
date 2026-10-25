import 'package:flutter/material.dart';
import 'models/diagnostic_report.dart';
import 'screens/dashboard_screen.dart';
import 'screens/document_scanner_screen.dart';
import 'screens/lab_reader_screen.dart';
import 'screens/clinical_assistant_screen.dart';
import 'screens/cardiac_monitor_screen.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const PranaScanApp());
}

class PranaScanApp extends StatelessWidget {
  const PranaScanApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PranaScan AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const MainNavigationShell(),
    );
  }
}

class MainNavigationShell extends StatefulWidget {
  const MainNavigationShell({super.key});

  @override
  State<MainNavigationShell> createState() => _MainNavigationShellState();
}

class _MainNavigationShellState extends State<MainNavigationShell> {
  int _currentIndex = 0;
  DiagnosticReport? _activeReport;

  void _onReportValidated(DiagnosticReport report) {
    setState(() {
      _activeReport = report;
      _currentIndex = 2; // Auto-forward to Lab Reader (Module 02)
    });
  }

  void _onConsultCopilot(DiagnosticReport report) {
    setState(() {
      _activeReport = report;
      _currentIndex = 3; // Switch to Clinical Copilot (Module 03)
    });
  }

  void _navigateToTab(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final List<Widget> screens = [
      DashboardScreen(onNavigateToTab: _navigateToTab),
      DocumentScannerScreen(onReportValidated: _onReportValidated),
      LabReaderScreen(
        currentReport: _activeReport,
        onConsultCopilot: _onConsultCopilot,
      ),
      ClinicalAssistantScreen(currentReport: _activeReport),
      const CardiacMonitorScreen(),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.transparent,
        elevation: 6,
        indicatorColor: AppTheme.primaryGreen.withValues(alpha: 0.15),
        onDestinationSelected: (int index) {
          setState(() {
            _currentIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.dashboard_outlined),
            selectedIcon: Icon(Icons.dashboard_rounded, color: AppTheme.primaryGreen),
            label: 'Dashboard',
          ),
          NavigationDestination(
            icon: Icon(Icons.document_scanner_outlined),
            selectedIcon: Icon(Icons.document_scanner_rounded, color: AppTheme.primaryGreen),
            label: 'Intake',
          ),
          NavigationDestination(
            icon: Icon(Icons.table_chart_outlined),
            selectedIcon: Icon(Icons.table_chart_rounded, color: AppTheme.primaryGreen),
            label: 'Lab Reader',
          ),
          NavigationDestination(
            icon: Icon(Icons.smart_toy_outlined),
            selectedIcon: Icon(Icons.smart_toy_rounded, color: AppTheme.primaryGreen),
            label: 'Copilot',
          ),
          NavigationDestination(
            icon: Icon(Icons.monitor_heart_outlined),
            selectedIcon: Icon(Icons.monitor_heart_rounded, color: AppTheme.primaryGreen),
            label: 'Telemetry',
          ),
        ],
      ),
    );
  }
}
