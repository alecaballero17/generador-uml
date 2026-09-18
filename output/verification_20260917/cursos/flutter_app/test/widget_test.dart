import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:cursos_demo/main.dart';

void main() {
  testWidgets('Carga inicial de la aplicación CursosDemo', (WidgetTester tester) async {
    await tester.pumpWidget(const UMLGeneratedApp());
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
