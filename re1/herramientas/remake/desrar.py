"""desrar.py archivo.rar destino : extrae con libarchive (ctypes)"""
import ctypes, sys, os
la = ctypes.CDLL('/nix/store/hd3akpv03rsvr62h5yk68xxq330mrlx8-libarchive-3.8.4-lib/lib/libarchive.so.13')
la.archive_read_new.restype = ctypes.c_void_p
la.archive_entry_pathname.restype = ctypes.c_char_p; la.archive_entry_pathname.argtypes = [ctypes.c_void_p]
la.archive_read_data.restype = ctypes.c_ssize_t; la.archive_read_data.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t]
for f in ('archive_read_support_format_all', 'archive_read_support_filter_all'): getattr(la, f).argtypes = [ctypes.c_void_p]
la.archive_read_open_filename.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
la.archive_read_next_header.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
la.archive_error_string.restype = ctypes.c_char_p; la.archive_error_string.argtypes = [ctypes.c_void_p]
a = la.archive_read_new(); la.archive_read_support_format_all(a); la.archive_read_support_filter_all(a)
if la.archive_read_open_filename(a, sys.argv[1].encode(), 1 << 20) != 0: sys.exit('no se pudo abrir: ' + str(la.archive_error_string(a)))
e = ctypes.c_void_p(); buf = ctypes.create_string_buffer(1 << 20)
while la.archive_read_next_header(a, ctypes.byref(e)) == 0:
    nm = la.archive_entry_pathname(e).decode('utf8', 'replace'); dst = os.path.join(sys.argv[2], nm)
    if nm.endswith('/') or os.path.isdir(dst): continue
    os.makedirs(os.path.dirname(dst) or '.', exist_ok=True); tot = 0
    with open(dst, 'wb') as fo:
        while True:
            n = la.archive_read_data(a, buf, len(buf))
            if n < 0: print('error', nm, la.archive_error_string(a)); break
            if n == 0: break
            fo.write(buf.raw[:n]); tot += n
    print(nm, tot)
