template = r"""
%% UTILS %%
\let\ex=\expandafter
\def\eat#1{}
\def\letcs#1#2{\ex\ex\ex \let\ex\ex \csname#1\endcsname \csname#2\endcsname}
\def\defcs#1#2{\def\defcstmp{#2}\letcs{#1}{defcstmp}}

\def\for#1#2#3#4{%
\if\in#2%
\defcs{endloop#1}{}%
\ex\def\csname loop#1\endcsname##1{%
\ex\ifx\csname endloop#1\endcsname##1\else%
\defcs{#1}{##1}%
#4\relax%
\letcs{looptmp}{loop#1}%
\ex\ex\ex\looptmp\fi}%
\letcs{looptmp}{loop#1}%
\ex\looptmp#3\csname endloop#1\endcsname%
\else%
\csname count#1\endcsname #2\relax%
\defcs{loop#1}{%
#4\relax%
\advance\csname count#1\endcsname 1\relax%
\ifnum\csname count#1\endcsname<#3%
\letcs{looptmp}{loop#1}%
\ex\ex\ex\looptmp\fi}\csname loop#1\endcsname%
\fi%
}

\def\nl{\par}

%% Colors %% (from ucwmac (c) MJ)
\chardef\colorstk=\pdfcolorstackinit page direct{0 g 0 G}
\def\colorset#1{\pdfcolorstack\colorstk set #1}
\def\colorpush#1{\pdfcolorstack\colorstk push #1}
\def\colorpop{\pdfcolorstack\colorstk pop}
\def\colorlocal{\aftergroup\colorpop\colorpush}
\def\rgb#1{{#1 rg #1 RG}}
\def\gray#1{{#1 g #1 G}}
\def\cmyk#1{{#1 k #1 K}}
\def\cwhite{\rgb{1 1 1}}

%% TMP vars %%
\newcount\counti
\newcount\countj
\let\isPrintNumpad\YES
\newdimen\keyw
\newdimen\keyh
\newdimen\skipBefore

\newinsert\marg
\newcount\margCount

%% Output %%
\def\pagebody{\vbox{\boxmaxdepth\maxdepth \pagecontents}}

\parindent=0pt
\hsize=86cm
\pdfpagewidth=87cm
\vsize=123cm
\pdfpageheight=0cm
\font\hhdfont csbx32
\font\smallfont cmr8
\font\basicfont cmr10\basicfont
\def\basebaselineskip{12pt} \baselineskip\basebaselineskip
\font\smallsmallfont cmr5 at 5pt
\newbox\autofontBox
\def\autofont#1{%
\setbox\autofontBox=\hbox{#1}%
\ifdim\wd\autofontBox<120pt\relax\basicfont\else%
\ifdim\wd\autofontBox<330pt\relax\baselineskip 1pt\smallfont\else%
\baselineskip 1pt\smallsmallfont\fi\fi%
#1\basicfont%
}%

\long\def\Mode#1#2{
{
\def\ModeName{#1}
#2
\vfil \break
}
}


%% Keyboard layout %%
\def\setkeywh#1#2#3#4{%
\defcs{keywK#1}{#2}%
\defcs{keyhK#1}{#3}%
\defcs{skipBeforeK#1}{#4}%
}

\def\Key#1#2#3{#2x#3}

\newdimen\standkeyw\standkeyw 100pt\relax%
\newdimen\standkeyh\standkeyh 35pt\relax%
\for i 0 {16}{\for j 0 {13} {\setkeywh{\Key{}{\the\counti}{\the\countj}}{\standkeyw}{\standkeyh}{0pt}}}


\setkeywh{0x1}{\standkeyw}{\standkeyh}{\standkeyw}
\setkeywh{0x5}{\standkeyw}{\standkeyh}{0.5\standkeyw}
\setkeywh{0x9}{\standkeyw}{\standkeyh}{0.5\standkeyw}
\setkeywh{1x13}{2\standkeyw}{\standkeyh}{0pt}
\setkeywh{2x0}{1.5\standkeyw}{\standkeyh}{0pt}
\setkeywh{2x13}{1.5\standkeyw}{\standkeyh}{0pt}
\setkeywh{3x0}{2\standkeyw}{\standkeyh}{0pt}
\setkeywh{4x0}{1.5\standkeyw}{\standkeyh}{0pt}
\setkeywh{4x12}{2.5\standkeyw}{\standkeyh}{0pt}
\setkeywh{5x0}{2\standkeyw}{\standkeyh}{0pt}
\setkeywh{5x1}{1.5\standkeyw}{\standkeyh}{0pt}
\setkeywh{5x2}{1.5\standkeyw}{\standkeyh}{0pt}
\setkeywh{5x3}{5\standkeyw}{\standkeyh}{0pt}
\setkeywh{5x4}{1.5\standkeyw}{\standkeyh}{0pt}
\setkeywh{5x5}{1.5\standkeyw}{\standkeyh}{0pt}
\setkeywh{5x6}{2\standkeyw}{\standkeyh}{0pt}
\setkeywh{9x0}{\standkeyw}{\standkeyh}{\standkeyw}
\setkeywh{15x0}{2\standkeyw}{\standkeyh}{0pt}
\defcs{keyLineLen0}{13}
\defcs{keyLineLen1}{14}
\defcs{keyLineLen2}{14}
\defcs{keyLineLen3}{13}
\defcs{keyLineLen4}{13}
\defcs{keyLineLen5}{07}
\defcs{keyLineLen6}{03}
\defcs{keyLineLen7}{03}
\defcs{keyLineLen8}{03}
\defcs{keyLineLen9}{01}
\defcs{keyLineLen10}{03}
\defcs{keyLineLen11}{04}
\defcs{keyLineLen12}{04}
\defcs{keyLineLen13}{03}
\defcs{keyLineLen14}{04}
\defcs{keyLineLen15}{02}


\newdimen\afterEscSkip
\afterEscSkip 30pt
\newdimen\afterAlphaSkip
\afterAlphaSkip 30pt


%% Core functions %%
\def\printbox#1#2{
\hrule \hbox{%
\vrule\relax%
\hbox to 0pt{\colorlocal{#1}\vrule width \keyw height \keyh\hskip -\keyw}%
\vbox to \keyh{%
\hsize\keyw%
\leftskip 0pt plus 1fill%
\rightskip 0pt plus 1fill%
\vskip 0pt plus 1fil\relax%
#2%
\hskip 0pt\hbox{}\vskip 0pt plus 1fil\relax\hrule height 0pt
}\vrule%
}\hrule%
\vskip -0.4pt
}

\def\printkey#1#2{%
\printbox{#1}{
\if\printActKeyIsFirst1\relax%
\keyname\nl%
\fi
#2%
}

\if\printActKeyIsFirst1\relax%
\advance\keyh -10pt%
\fi
\def\printActKeyIsFirst{0}
}

\def\printActKey{\relax%
\def\keyBase{\the\counti x\the\countj}\relax
\skipBefore \csname skipBeforeK\keyBase\endcsname\relax%
\kern \skipBefore\vbox{%
\keyw \csname keywK\keyBase\endcsname%
\keyh \csname keyhK\keyBase\endcsname%
\advance\keyw -0.4pt%
\advance\keyh -0.4pt%
\def\printActKeyIsFirst{1}
\csname key\keyBase\endcsname \vskip1pt
}%
\hskip -0.4pt
}

\def\modificatorbox#1{
\printbox{\rgb{1 1 1}}{#1}%
\if \printActKeyIsFirst1\relax%
\advance\keyh -10pt%
\def\printActKeyIsFirst{0}%
\fi%
}

\def\printModList{%
\kern \skipBefore\vbox{%
\keyw 0.4\standkeyw%
\keyh \standkeyh%
\advance\keyw -0.4pt%
\advance\keyh -0.4pt%
\def\keyname{}%
\def\printActKeyIsFirst{1}
\modlist
}%
\hskip -0.4pt
\hskip 20pt
}


\def\printLine#1#2{%
\hbox{#2%
\for j 0 {\csname keyLineLen\the\counti\endcsname}%
\printActKey
}%
\vskip 10pt%
}

\newbox\outbox

\def\isFirstPrintKeyboard{1}

\def\PrintKeyboard{
\if\isFirstPrintKeyboard 1
\def\isFirstPrintKeyboard{0}
{\hhdfont \ModeName }%
\vskip 15pt\relax
\else
\vskip 50pt\relax
\fi
\hbox{
\vbox{
\for i 0 1{\printLine{\the\counti}{\printModList}}
\vskip\afterEscSkip\relax
\for i 1 6{\printLine{\the\counti}{\printModList}}
}\hskip \afterAlphaSkip
\vbox{
\for i 6 7{\printLine{\the\counti}{}}
\vskip\afterEscSkip\relax
\for i 7 9{\printLine{\the\counti}{}}
% { \setbox5=\vbox{\Key{}{0}{0}\printActKey}\vskip\ht5}
\for i 9 {11}{\printLine{\the\counti}{}}
}
\ifx\isPrintNumpad\YES
\hskip \afterAlphaSkip
\vbox{
\for i {11} {16}{\printLine{\the\counti}{}}
}
\else
\fi
}
}

\def\printemptykey{\printkey{\rgb{1 1 1}}{}}

%% Redefien for python input
\catcode91=1
\catcode93=2
\catcode36=0
\catcode123=12
\catcode125=12
\catcode38=12
\catcode94=12
\catcode95=12
\catcode37=12
"""
