import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:__PACKAGE__/main.dart';

void main() {
  testWidgets('Inicio compacto, navegacion y formulario accesible', (tester) async {
    SharedPreferences.setMockInitialValues({});
    tester.view.physicalSize = const Size(360, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const UMLGeneratedApp());
    await tester.pump(const Duration(seconds: 4));
    expect(find.text('Nuevo registro'), findsOneWidget);
    expect(find.textContaining('Asistente'), findsNothing);
    if (__HAS_MODULES__) {
    await tester.tap(find.text('Nuevo registro'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(ListTile, __FIRST_MODULE__));
    await tester.pumpAndSettle();
    expect(find.text('Crear registro'), findsOneWidget);
    expect(find.byType(Form), findsOneWidget);
    final button = tester.getRect(find.text('Crear registro'));
    expect(button.bottom, lessThan(800));
    }
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump(const Duration(seconds: 4));
  });
}
