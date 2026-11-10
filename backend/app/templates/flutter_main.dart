import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'screens/dashboard_screen.dart';
import 'services/api_config.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiConfig.load();
  runApp(const UMLGeneratedApp());
}

class UMLGeneratedApp extends StatefulWidget {
  const UMLGeneratedApp({super.key});
  @override
  State<UMLGeneratedApp> createState() => _UMLGeneratedAppState();
}

class _UMLGeneratedAppState extends State<UMLGeneratedApp> {
  ThemeMode _themeMode = ThemeMode.dark;
  @override
  void initState() {
    super.initState();
    SharedPreferences.getInstance().then((prefs) {
      if (mounted) setState(() => _themeMode = prefs.getString('app_theme') == 'light' ? ThemeMode.light : ThemeMode.dark);
    });
  }
  void _toggleTheme() {
    setState(() => _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark);
    SharedPreferences.getInstance().then((prefs) => prefs.setString('app_theme', _themeMode == ThemeMode.dark ? 'dark' : 'light'));
  }
  ThemeData _theme(Brightness brightness) {
    final dark = brightness == Brightness.dark;
    final scheme = ColorScheme.fromSeed(seedColor: const Color(0xFF9873E9), brightness: brightness).copyWith(
      primary: dark ? const Color(0xFFC4ADFF) : const Color(0xFF7652BF),
      surface: dark ? const Color(0xFF1D2030) : Colors.white,
      background: dark ? const Color(0xFF111420) : const Color(0xFFF6F7FB),
    );
    return ThemeData(
      useMaterial3: true, brightness: brightness, colorScheme: scheme,
      scaffoldBackgroundColor: scheme.background,
      appBarTheme: AppBarTheme(backgroundColor: scheme.background, foregroundColor: scheme.onSurface, surfaceTintColor: Colors.transparent, centerTitle: false, elevation: 0, titleTextStyle: TextStyle(color: scheme.onSurface, fontSize: 19, fontWeight: FontWeight.w700)),
      cardTheme: CardTheme(color: scheme.surface, surfaceTintColor: Colors.transparent, elevation: 0, margin: EdgeInsets.zero, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20), side: BorderSide(color: scheme.outlineVariant.withOpacity(.3)))),
      inputDecorationTheme: InputDecorationTheme(filled: true, fillColor: scheme.surface, contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 18), border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.outlineVariant)), enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: BorderSide(color: scheme.outlineVariant.withOpacity(.5)))),
      filledButtonTheme: FilledButtonThemeData(style: FilledButton.styleFrom(minimumSize: const Size(48, 50), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)), textStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15))),
      floatingActionButtonTheme: FloatingActionButtonThemeData(backgroundColor: dark ? const Color(0xFF9E7ADA) : const Color(0xFF7652BF), foregroundColor: Colors.white, elevation: 3, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(17))),
      listTileTheme: const ListTileThemeData(contentPadding: EdgeInsets.symmetric(horizontal: 18, vertical: 8)),
      navigationBarTheme: NavigationBarThemeData(backgroundColor: scheme.surface, indicatorColor: scheme.primary.withOpacity(.16), labelTextStyle: MaterialStateProperty.all(const TextStyle(fontSize: 12, fontWeight: FontWeight.w600))),
      snackBarTheme: SnackBarThemeData(behavior: SnackBarBehavior.floating, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
    );
  }
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: __TITLE__, debugShowCheckedModeBanner: false,
    themeMode: _themeMode, theme: _theme(Brightness.light), darkTheme: _theme(Brightness.dark),
    home: DashboardScreen(onToggleTheme: _toggleTheme),
  );
}
