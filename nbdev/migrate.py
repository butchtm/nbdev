# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/15_migrate.ipynb.

# %% auto 0
__all__ = ['nb_alias_fm', 'convert_callout', 'repl_v1dir', 'migrate_nb', 'migrate_md', 'nbdev_migrate']

# %% ../nbs/15_migrate.ipynb 2
from .process import first_code_ln
from .read import *
from .processors import yml2dict, filter_fm
from .read import read_nb, config_key
from .sync import write_nb
from .clean import process_write
from .showdoc import show_doc
from fastcore.all import *
import shutil

# %% ../nbs/15_migrate.ipynb 4
def _cat_slug(d):
    "Get the partial slug from the category front matter."
    slug = '/'.join(sorted(d.get('categories', '')))
    return '/' + slug if slug else ''

# %% ../nbs/15_migrate.ipynb 6
def _file_slug(fname): 
    "Get the partial slug from the filename."
    p = Path(fname)
    dt = '/'+p.name[:10].replace('-', '/')+'/'
    return dt + p.stem[11:]    

# %% ../nbs/15_migrate.ipynb 8
_re_dt = re.compile(r'^\d{4}-\d{2}-\d{2}')

def _alias(fm:dict, p:Path):
    p = Path(p)
    if not _re_dt.search(p.name): return {}
    return {'aliases': [f"{fm.pop('permalink').strip()}"] if 'permalink' in fm else [f'{_cat_slug(fm) + _file_slug(p)}']}

# %% ../nbs/15_migrate.ipynb 9
def nb_alias_fm(path):
    "Fix slugs for fastpages and jekyll compatibility."
    nb = NB(path)
    nb.update_raw_fm(_alias(nb.fmdict, path)) #use the combined markdown & raw front matter to determine the alias
    return nb

# %% ../nbs/15_migrate.ipynb 13
_re_callout = re.compile(r'^>\s(Warning|Note|Important|Tip):(.*)', flags=re.MULTILINE)
def _co(x): return "\n:::{.callout-"+x[1].lower()+"}\n\n" + f"{x[2].strip()}\n\n" + ":::\n"
def convert_callout(s): 
    "Convert nbdev v1 to v2 callouts."
    return _re_callout.sub(_co, s)

# %% ../nbs/15_migrate.ipynb 18
def _listify(s): return s.splitlines() if type(s) == str else s

def _nb_repl_callouts(nb):
    "Replace nbdev v1 with v2 callouts."
    for cell in nb['cells']:
        if cell.get('source') and cell.get('cell_type') == 'markdown':
            cell['source'] = ''.join([convert_callout(c) for c in _listify(cell['source'])])
    return nb

# %% ../nbs/15_migrate.ipynb 21
_dirmap = merge({k:'code-fold: true' for k in ['collapse', 'collapse_input', 'collapse_hide']}, {'collapse_show':'code-fold: show'})
def _subv1(s): return _dirmap.get(s, s)

# %% ../nbs/15_migrate.ipynb 22
def _re_v1():
    d = ['default_exp', 'export', 'exports', 'exporti', 'hide', 'hide_input', 'collapse_show', 'collapse',
         'collapse_hide', 'collapse_input', 'hide_output',  'default_cls_lvl']
    d += L(config_key('tst_flags', path=False)).filter()
    d += [s.replace('_', '-') for s in d] # allow for hyphenated version of old directives
    _tmp = '|'.join(list(set(d)))
    return re.compile(f"^[ \f\v\t]*?(#)\s*({_tmp})(?!\S)", re.MULTILINE)

def _repl_directives(code_str): 
    def _fmt(x): return f"#| {_subv1(x[2].replace('-', '_').strip())}"
    return _re_v1().sub(_fmt, code_str)

# %% ../nbs/15_migrate.ipynb 25
def repl_v1dir(nb):
    "Replace nbdev v1 with v2 directives."
    for cell in nb['cells']:
        if cell.get('source') and cell.get('cell_type') == 'code':
            ss = listify(cell['source'])
            first_code = first_code_ln(ss, re_pattern=_re_v1())
            if not first_code: first_code = len(ss)
            if not ss: pass
            else: cell['source'] = ''.join([_repl_directives(c) for c in ss[:first_code]] + ss[first_code:])
    return nb

# %% ../nbs/15_migrate.ipynb 32
def migrate_nb(path, overwrite=False):
    "Migrate nbdev v1 and fastpages notebooks to nbdev v2."
    nb = compose(nb_alias_fm, _nb_repl_callouts, repl_v1dir)(path)
    if overwrite: 
        write_nb(nb.nb, path)
    return nb

# %% ../nbs/15_migrate.ipynb 37
_re_fm_md = re.compile(r'^---(.*\S+.)?---', flags=re.DOTALL)

def _md_fmdict(txt):
    "Get front matter as a dict from a markdown file."
    m = _re_fm_md.match(txt)
    return yml2dict(m.group(1)) if m else {}

# %% ../nbs/15_migrate.ipynb 39
def migrate_md(path, overwrite=False):
    "Make fastpages front matter in markdown files quarto compliant."
    p = Path(path)
    md = p.read_text()
    fm = _md_fmdict(md)
    if fm:
        fm = filter_fm(merge(_alias(fm, p), fm))
        txt = _re_fm_md.sub(dict2fm(fm), md)
        if overwrite: p.write_text(txt)
        return txt
    else: return md 

# %% ../nbs/15_migrate.ipynb 45
@call_parse
def nbdev_migrate(
    path:str = '.', # A path to search
    file_glob:str = '*.ipynb', # A file glob
    no_skip:bool=False, # Do not skip directories beginning with an underscore
):
    "Convert all directives and callouts in `fname` from v1 to v2"
    _skip_re = None if no_skip else '^[_.]'
    if path is None: path = config_key("nbs_path")
    if Path(path).is_file(): file_glob=None
    for f in globtastic(path, file_glob=file_glob, skip_folder_re=_skip_re): 
        if f.suffix == '.ipynb': migrate_nb(f, overwrite=True)
        if f.suffix == '.md': migrate_md(f, overwrite=True)
