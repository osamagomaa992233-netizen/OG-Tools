OG TOOLS v0.8 - WINDOWS INSTALLER KIT

الموجود هنا: سورس الإضافة + محرك المعالجة + سكريبت تثبيت تلقائي + إعداد GitHub لبناء محرك Windows مستقل.

لو عندك Windows 10/11: فك الضغط، ثم شغّل INSTALL_OG_TOOLS.cmd. ده هيحاول يجهز Python وFFmpeg وWhisper تلقائيًا ويحط ملفات البانل في مجلد UXP.

مهم: ده إصدار هندسي، مش منتج نهائي مختبر داخل Premiere. تثبيت البانل بمجلد External مش هو مسار CCX الرسمي؛ مش مضمون Premiere يتعرف عليه.

الأفضل لتقليل التثبيت: شغّل Workflow build-windows-portable.yml على GitHub، هينتج ZIP فيه محرك EXE مستقل بعد نجاح الاختبارات. لم يتم تشغيل الـWorkflow هنا.

Whisper محتاج تحميل الموديل أول مرة. قص السكوت والـSpeed Ramp بيصدروا نسخ فيديو منفصلة، مش تعديل أصلي على التايملاين. الـZoom Keyframes لم يختبر في Premiere فعليًا.
