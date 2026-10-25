import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // Bespoke Editorial Botanical Palette
  static const Color primaryGreen = Color(0xFF1B5234);
  static const Color forestDark = Color(0xFF0F291A);
  static const Color deepBackground = Color(0xFF07170E);
  static const Color tealAccent = Color(0xFF10B981);
  static const Color lightTeal = Color(0xFF34D399);
  static const Color lightBg = Color(0xFFFAFBF9);
  static const Color surfaceWhite = Color(0xFFFFFFFF);
  static const Color borderSubtle = Color(0xFFE3E7E3);
  static const Color textDark = Color(0xFF121D17);
  static const Color textMuted = Color(0xFF687A70);
  static const Color alertDanger = Color(0xFFB91C1C);
  static const Color alertDangerBg = Color(0xFFFEF2F2);
  static const Color alertWarning = Color(0xFFB45309);
  static const Color alertWarningBg = Color(0xFFFFFBEB);
  static const Color alertSuccessBg = Color(0xFFF0FDF4);

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryGreen,
        primary: primaryGreen,
        surface: surfaceWhite,
        background: lightBg,
      ),
      scaffoldBackgroundColor: lightBg,
      textTheme: GoogleFonts.plusJakartaSansTextTheme().copyWith(
        displayLarge: GoogleFonts.newsreader(fontWeight: FontWeight.w600, color: textDark, fontSize: 32),
        headlineLarge: GoogleFonts.newsreader(fontWeight: FontWeight.w600, color: textDark, fontSize: 26),
        headlineMedium: GoogleFonts.newsreader(fontWeight: FontWeight.w500, color: textDark, fontSize: 22),
        titleLarge: GoogleFonts.newsreader(fontWeight: FontWeight.w600, color: textDark, fontSize: 18),
        titleMedium: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w600, color: textDark, fontSize: 15),
        bodyLarge: GoogleFonts.plusJakartaSans(color: textDark, fontSize: 15, height: 1.5),
        bodyMedium: GoogleFonts.plusJakartaSans(color: textMuted, fontSize: 13.5, height: 1.5),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: surfaceWhite,
        elevation: 0,
        surfaceTintColor: Colors.transparent,
        iconTheme: const IconThemeData(color: textDark),
        titleTextStyle: GoogleFonts.newsreader(
          color: textDark,
          fontSize: 20,
          fontWeight: FontWeight.w600,
        ),
      ),
      cardTheme: CardTheme(
        color: surfaceWhite,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
          side: const BorderSide(color: borderSubtle, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryGreen,
          foregroundColor: Colors.white,
          elevation: 0,
          padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 14),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          textStyle: GoogleFonts.plusJakartaSans(
            fontWeight: FontWeight.w600,
            fontSize: 14,
            letterSpacing: 0.2,
          ),
        ),
      ),
    );
  }
}
