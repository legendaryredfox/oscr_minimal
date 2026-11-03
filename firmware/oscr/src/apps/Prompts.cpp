#include "common.h"
#include "api.h"

#include "ui.h"

#include "apps/Prompts.h"

namespace OSCR::Prompts
{
  constexpr char const * const PROGMEM abortRetryContinueOptions[] = {
    OSCR::Strings::MenuOptions::Abort,
    OSCR::Strings::MenuOptions::Retry,
    OSCR::Strings::MenuOptions::Continue,
  };

  constexpr char const * const PROGMEM confirmEraseOptions[] = {
    OSCR::Strings::MenuOptions::Back,
    OSCR::Strings::MenuOptions::Erase,
  };

  constexpr char const * const PROGMEM askYesNoOptions[] = {
    OSCR::Strings::MenuOptions::Yes,
    OSCR::Strings::MenuOptions::No,
  };

  AbortRetryContinue abortRetryContinue()
  {
# if OSCR_DUMPER
    return AbortRetryContinue::Abort;   // fork oscr_minimal: sem usuário; o comando termina com erro
# endif
    return static_cast<AbortRetryContinue>(OSCR::UI::menu(FS(OSCR::Strings::Headings::CartridgeError), abortRetryContinueOptions, sizeofarray(abortRetryContinueOptions)));
  }

  bool confirmErase()
  {
# if OSCR_DUMPER
    return true;   // fork oscr_minimal: o PC já pediu a confirmação (GUI e CLI)
# endif
    return (OSCR::UI::menu(FS(OSCR::Strings::Headings::ConfirmErase), confirmEraseOptions, sizeofarray(confirmEraseOptions)) == 1);
  }

  bool askYesNo(char const * question)
  {
# if OSCR_DUMPER
    (void)question;
    return false;
# endif
    return (OSCR::UI::menu(FS(question), askYesNoOptions, sizeofarray(askYesNoOptions)) == 0);
  }
}
