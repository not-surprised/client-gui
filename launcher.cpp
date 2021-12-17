#include <Windows.h>

LPWSTR GetCurrentDirectory()
{
    auto buffer = new wchar_t [MAX_PATH];
    GetModuleFileNameW(nullptr, buffer, MAX_PATH);
    wchar_t *c = buffer;
    wchar_t *ptr = c;
    while (*ptr) {
        if (*ptr == '\\' || *ptr == '/') {
            c = ptr;
        }
        ptr++;
    }
    *c = '\0';
    return c;
}

int WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, PSTR lpCmdLine, int nCmdShow)
{
    SHELLEXECUTEINFOW info = {0};
    info.cbSize = sizeof(SHELLEXECUTEINFOW);
    info.fMask = SEE_MASK_NOCLOSEPROCESS;
    info.hwnd = nullptr;
    info.lpVerb = nullptr;
    info.lpFile = L"cmd.exe";
    info.lpParameters = LR"(/c "run.cmd")";
    info.lpDirectory = GetCurrentDirectory();
    info.nShow = SW_HIDE;
    info.hInstApp = nullptr;
    ShellExecuteExW(&info);
#ifdef WAIT_UNTIL_TERMINATE
    WaitForSingleObject(info.hProcess, INFINITE);
#endif
    CloseHandle(info.hProcess);

    return 0;
}
