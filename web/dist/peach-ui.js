import { LOC as e, fmtDur as t, fmtSize as n } from "/js/core.js";
import { emptyStateHtml as r, noteHtml as i } from "/js/ui-components.js";
//#region node_modules/preact/dist/preact.module.js
var a, o, s, c, l, u, d, f, p, m, h, g, _, v, y, b = {}, x = [], S = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, C = Array.isArray;
function w(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function ee(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function T(e, t, n) {
	var r, i, o, s = {};
	for (o in t) o == "key" ? r = t[o] : o == "ref" ? i = t[o] : s[o] = t[o];
	if (arguments.length > 2 && (s.children = arguments.length > 3 ? a.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (o in e.defaultProps) s[o] === void 0 && (s[o] = e.defaultProps[o]);
	return E(e, s, r, i, null);
}
function E(e, t, n, r, i) {
	var a = {
		type: e,
		props: t,
		key: n,
		ref: r,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: i ?? ++s,
		__i: -1,
		__u: 0
	};
	return i == null && o.vnode != null && o.vnode(a), a;
}
function D(e) {
	return e.children;
}
function O(e, t) {
	this.props = e, this.context = t;
}
function k(e, t) {
	if (t == null) return e.__ ? k(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? k(e) : null;
}
function te(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = w({}, t);
		a.__v = t.__v + 1, o.vnode && o.vnode(a), le(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? k(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, de(r, a, i), t.__e = t.__ = null, a.__e != n && A(a);
	}
}
function A(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), A(e);
}
function j(e) {
	(!e.__d && (e.__d = !0) && l.push(e) && !M.__r++ || u != o.debounceRendering) && ((u = o.debounceRendering) || d)(M);
}
function M() {
	try {
		for (var e, t = 1; l.length;) l.length > t && l.sort(f), e = l.shift(), t = l.length, te(e);
	} finally {
		l.length = M.__r = 0;
	}
}
function ne(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || x, v = t.length;
	for (c = re(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || b, p.__i = d, g = le(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && me(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = ie(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function re(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = E(null, o, null, null, null) : C(o) ? o = e.__k[a] = E(D, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = E(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = ae(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = k(s)), he(s, s));
	return r;
}
function ie(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = ie(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = k(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function ae(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function oe(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || S.test(t) ? n : n + "px";
}
function se(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || oe(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || oe(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(g, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[h] = r[h] : (n[h] = _, e.addEventListener(t, a ? y : v, a)) : e.removeEventListener(t, a ? y : v, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function ce(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[m] == null) t[m] = _++;
			else if (t[m] < n[h]) return;
			return n(o.event ? o.event(t) : t);
		}
	};
}
function le(e, t, n, r, i, a, s, c, l, u) {
	var d, f, p, m, h, g, _, v, y, b, S, T, E, te, A, j, M = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (l = !!(32 & n.__u), a = [c = t.__e = n.__e]), (d = o.__b) && d(t);
	n: if (typeof M == "function") {
		f = s.length;
		try {
			if (y = t.props, b = M.prototype && M.prototype.render, S = (d = M.contextType) && r[d.__c], T = d ? S ? S.props.value : d.__ : r, n.__c ? v = (p = t.__c = n.__c).__ = p.__E : (b ? t.__c = p = new M(y, T) : (t.__c = p = new O(y, T), p.constructor = M, p.render = ge), S && S.sub(p), p.state || (p.state = {}), p.__n = r, m = p.__d = !0, p.__h = [], p._sb = []), b && p.__s == null && (p.__s = p.state), b && M.getDerivedStateFromProps != null && (p.__s == p.state && (p.__s = w({}, p.__s)), w(p.__s, M.getDerivedStateFromProps(y, p.__s))), h = p.props, g = p.state, p.__v = t, m) b && M.getDerivedStateFromProps == null && p.componentWillMount != null && p.componentWillMount(), b && p.componentDidMount != null && p.__h.push(p.componentDidMount);
			else {
				if (b && M.getDerivedStateFromProps == null && y !== h && p.componentWillReceiveProps != null && p.componentWillReceiveProps(y, T), t.__v == n.__v || !p.__e && p.shouldComponentUpdate != null && !1 === p.shouldComponentUpdate(y, p.__s, T)) {
					t.__v != n.__v && (p.props = y, p.state = p.__s, p.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), x.push.apply(p.__h, p._sb), p._sb = [], p.__h.length && s.push(p), c = k(n);
					break n;
				}
				p.componentWillUpdate != null && p.componentWillUpdate(y, p.__s, T), b && p.componentDidUpdate != null && p.__h.push(function() {
					p.componentDidUpdate(h, g, _);
				});
			}
			if (p.context = T, p.props = y, p.__P = e, p.__e = !1, E = o.__r, te = 0, b) p.state = p.__s, p.__d = !1, E && E(t), d = p.render(p.props, p.state, p.context), x.push.apply(p.__h, p._sb), p._sb = [];
			else do
				p.__d = !1, E && E(t), d = p.render(p.props, p.state, p.context), p.state = p.__s;
			while (p.__d && ++te < 25);
			p.state = p.__s, p.getChildContext != null && (r = w(w({}, r), p.getChildContext())), b && !m && p.getSnapshotBeforeUpdate != null && (_ = p.getSnapshotBeforeUpdate(h, g)), A = d != null && d.type === D && d.key == null ? fe(d.props.children) : d, c = ne(e, C(A) ? A : [A], t, n, r, i, a, s, c, l, u), p.base = t.__e, t.__u &= -161, p.__h.length && s.push(p), v && (p.__E = p.__ = null);
		} catch (e) {
			if (s.length = f, t.__v = null, l || a != null) {
				if (e.then) {
					for (t.__u |= l ? 160 : 128; c && c.nodeType == 8 && c.nextSibling;) c = c.nextSibling;
					a != null && (a[a.indexOf(c)] = null), t.__e = c;
				} else if (a != null) for (j = a.length; j--;) ee(a[j]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || ue(t), o.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : c = t.__e = pe(n.__e, t, n, r, i, a, s, l, u);
	return (d = o.diffed) && d(t), 128 & t.__u ? void 0 : c;
}
function ue(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(ue));
}
function de(e, t, n) {
	for (var r = 0; r < n.length; r++) me(n[r], n[++r], n[++r]);
	o.__c && o.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			o.__e(e, t.__v);
		}
	});
}
function fe(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : C(e) ? e.map(fe) : e.constructor === void 0 ? w({}, e) : null;
}
function pe(e, t, n, r, i, s, c, l, u) {
	var d, f, p, m, h, g, _, v = n.props || b, y = t.props, x = t.type;
	if (x == "svg" ? i = "http://www.w3.org/2000/svg" : x == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", s != null) {
		for (d = 0; d < s.length; d++) if ((h = s[d]) && "setAttribute" in h == !!x && (x ? h.localName == x : h.nodeType == 3)) {
			e = h, s[d] = null;
			break;
		}
	}
	if (e == null) {
		if (x == null) return document.createTextNode(y);
		e = document.createElementNS(i, x, y.is && y), l &&= (o.__m && o.__m(t, s), !1), s = null;
	}
	if (x == null) v === y || l && e.data == y || (e.data = y);
	else {
		if (s = x == "textarea" && y.defaultValue != null ? null : s && a.call(e.childNodes), !l && s != null) for (v = {}, d = 0; d < e.attributes.length; d++) v[(h = e.attributes[d]).name] = h.value;
		for (d in v) h = v[d], d == "dangerouslySetInnerHTML" ? p = h : d == "children" || d in y || d == "value" && "defaultValue" in y || d == "checked" && "defaultChecked" in y || se(e, d, null, h, i);
		for (d in y) h = y[d], d == "children" ? m = h : d == "dangerouslySetInnerHTML" ? f = h : d == "value" ? g = h : d == "checked" ? _ = h : l && typeof h != "function" || v[d] === h || se(e, d, h, v[d], i);
		if (f) l || p && (f.__html == p.__html || f.__html == e.innerHTML) || (e.innerHTML = f.__html), t.__k = [];
		else if (p && (e.innerHTML = ""), ne(t.type == "template" ? e.content : e, C(m) ? m : [m], t, n, r, x == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, s, c, s ? s[0] : n.__k && k(n, 0), l, u), s != null) for (d = s.length; d--;) ee(s[d]);
		l && x != "textarea" || (d = "value", x == "progress" && g == null ? e.removeAttribute("value") : g != null && (g !== e[d] || x == "progress" && !g || x == "option" && g != v[d]) && se(e, d, g, v[d], i), d = "checked", _ != null && _ != e[d] && se(e, d, _, v[d], i));
	}
	return e;
}
function me(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		o.__e(e, n);
	}
}
function he(e, t, n) {
	var r, i;
	if (o.unmount && o.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || me(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			o.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && he(r[i], t, n || typeof e.type != "function");
	n || ee(e.__e), e.__c = e.__ = e.__e = void 0;
}
function ge(e, t, n) {
	return this.constructor(e, n);
}
function _e(e, t, n) {
	var r, i, s, c;
	t == document && (t = document.documentElement), o.__ && o.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, s = [], c = [], le(t, e = (!r && n || t).__k = T(D, null, [e]), i || b, b, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? a.call(t.childNodes) : null, s, !r && n ? n : i ? i.__e : t.firstChild, r, c), de(s, e, c), e.props.children = null;
}
a = x.slice, o = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, s = 0, c = function(e) {
	return e != null && e.constructor === void 0;
}, O.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = w({}, this.state);
	typeof e == "function" && (e = e(w({}, n), this.props)), e && w(n, e), e != null && this.__v && (t && this._sb.push(t), j(this));
}, O.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), j(this));
}, O.prototype.render = D, l = [], d = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, f = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, M.__r = 0, p = Math.random().toString(8), m = "__d" + p, h = "__a" + p, g = /(PointerCapture)$|Capture$/i, _ = 0, v = ce(!1), y = ce(!0);
//#endregion
//#region src/api.ts
var ve = class extends Error {
	status;
	constructor(e, t) {
		super(e), this.name = "ApiError", this.status = t;
	}
}, ye = (e) => {
	if (!e || typeof e != "object") return "";
	let t = e;
	for (let e of [
		"message",
		"detail",
		"error"
	]) {
		let n = t[e];
		if (typeof n == "string" && n) return n;
	}
	return "";
}, be = (e) => e instanceof Error ? e.message : String(e);
async function xe(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new ve(ye(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var Se, N, Ce, we, Te = 0, Ee = [], P = o, De = P.__b, Oe = P.__r, ke = P.diffed, Ae = P.__c, je = P.unmount, Me = P.__;
function Ne(e, t) {
	P.__h && P.__h(N, e, Te || t), Te = 0;
	var n = N.__H || (N.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function Pe(e, t) {
	var n = Ne(Se++, 7);
	return ze(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function Fe() {
	for (var e; e = Ee.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(F), t.__h.some(Re), t.__h = [];
		} catch (n) {
			t.__h = [], P.__e(n, e.__v);
		}
	}
}
P.__b = function(e) {
	N = null, De && De(e);
}, P.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Me && Me(e, t);
}, P.__r = function(e) {
	Oe && Oe(e), Se = 0;
	var t = (N = e.__c).__H;
	t && (Ce === N ? (t.__h = [], N.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(F), t.__h.some(Re), t.__h = [], Se = 0)), Ce = N;
}, P.diffed = function(e) {
	ke && ke(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Ee.push(t) !== 1 && we === P.requestAnimationFrame || ((we = P.requestAnimationFrame) || Le)(Fe)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Ce = N = null;
}, P.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(F), e.__h = e.__h.filter(function(e) {
				return !e.__ || Re(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], P.__e(n, e.__v);
		}
	}), Ae && Ae(e, t);
}, P.unmount = function(e) {
	je && je(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			F(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && P.__e(t, n.__v));
};
var Ie = typeof requestAnimationFrame == "function";
function Le(e) {
	var t, n = function() {
		clearTimeout(r), Ie && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Ie && (t = requestAnimationFrame(n));
}
function F(e) {
	var t = N, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), N = t;
}
function Re(e) {
	var t = N;
	e.__c = e.__(), N = t;
}
function ze(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var Be = Symbol.for("preact-signals");
function Ve() {
	if (z > 1) z--;
	else {
		var e, t = !1;
		for ((function() {
			var e = V;
			for (V = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); R !== void 0;) {
			var n = R;
			for (R = void 0, B++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && Je(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (B = 0, z--, t) throw e;
	}
}
function He(e) {
	if (z > 0) return e();
	Ge = ++We, z++;
	try {
		return e();
	} finally {
		Ve();
	}
}
var I, L = void 0;
function Ue(e) {
	var t = L, n = I;
	L = void 0, I = void 0;
	try {
		return e();
	} finally {
		L = t, I = n;
	}
}
var R = void 0, z = 0, B = 0, We = 0, Ge = 0, V = void 0, H = 0;
function Ke(e) {
	if (L !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== L) return t = {
			i: 0,
			S: e,
			p: L.s,
			n: void 0,
			t: L,
			e: void 0,
			x: void 0,
			r: t
		}, L.s !== void 0 && (L.s.n = t), L.s = t, e.n = t, 32 & L.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = L.s, t.n = void 0, L.s.n = t, L.s = t), t;
	}
}
function U(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
U.prototype.brand = Be, U.prototype.h = function() {
	return !0;
}, U.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? Ue(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, U.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && Ue(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, U.prototype.subscribe = function(e) {
	var t = this;
	return q(function() {
		var n = t.value;
		Ue(function() {
			return e(n);
		});
	}, { name: "sub" });
}, U.prototype.valueOf = function() {
	return this.value;
}, U.prototype.toString = function() {
	return this.value + "";
}, U.prototype.toJSON = function() {
	return this.value;
}, U.prototype.peek = function() {
	var e = this;
	return Ue(function() {
		return e.value;
	});
}, Object.defineProperty(U.prototype, "value", {
	get: function() {
		var e = Ke(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (B > 100) throw Error("Cycle detected");
			(function(e) {
				z !== 0 && B === 0 && e.l !== Ge && (e.l = Ge, V = {
					S: e,
					v: e.v,
					i: e.i,
					o: V
				});
			})(this), this.v = e, this.i++, H++, z++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				Ve();
			}
		}
	}
});
function qe(e, t) {
	return new U(e, t);
}
function Je(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function Ye(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function Xe(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function W(e, t) {
	U.call(this, void 0, t), this.x = e, this.s = void 0, this.g = H - 1, this.f = 4;
}
W.prototype = new U(), W.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === H)) return !0;
	if (this.g = H, this.f |= 1, this.i > 0 && !Je(this)) return this.f &= -2, !0;
	var e = L;
	try {
		Ye(this), L = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return L = e, Xe(this), this.f &= -2, !0;
}, W.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	U.prototype.S.call(this, e);
}, W.prototype.U = function(e) {
	if (this.t !== void 0 && (U.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, W.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(W.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = Ke(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function G(e, t) {
	return new W(e, t);
}
function Ze(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		z++;
		var n = L;
		L = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, Qe(e), t;
		} finally {
			L = n, Ve();
		}
	}
}
function Qe(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, Ze(e);
}
function $e(e) {
	if (L !== this) throw Error("Out-of-order effect");
	Xe(this), L = e, this.f &= -2, 8 & this.f && Qe(this), Ve();
}
function K(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, I && I.push(this);
}
K.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, K.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, Ze(this), Ye(this), z++;
	var e = L;
	return L = this, $e.bind(this, e);
}, K.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = R, R = this);
}, K.prototype.d = function() {
	this.f |= 8, 1 & this.f || Qe(this);
}, K.prototype.dispose = function() {
	this.d();
};
function q(e, t) {
	var n = new K(e, t);
	try {
		n.c();
	} catch (e) {
		throw n.d(), e;
	}
	var r = n.d.bind(n);
	return r[Symbol.dispose] = r, r;
}
//#endregion
//#region node_modules/@preact/signals/dist/signals.module.js
var et, J, tt = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, nt = [];
q(function() {
	et = this.N;
})();
function Y(e, t) {
	o[e] = t.bind(null, o[e] || function() {});
}
function X(e) {
	if (J) {
		var t = J;
		J = void 0, t();
	}
	J = e && e.S();
}
function rt(e) {
	var t = this, n = e.data, r = at(n);
	r.name = "ReactiveDom", r.value = n;
	var i = Pe(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = G(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = G(function() {
			return !Array.isArray(i.value) && !c(i.value);
		}), o = q(function() {
			if (this.N = ct, a.value) {
				var t = i.value;
				e.__v && e.__v.__e && e.__v.__e.nodeType === 3 && (e.__v.__e.data = t);
			}
		}), s = t.__$u.d;
		return t.__$u.d = function() {
			o(), s.call(this);
		}, [a, i];
	}, []), a = i[0], o = i[1];
	return a.value ? o.peek() : o.value;
}
rt.displayName = "ReactiveTextNode", Object.defineProperties(U.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: rt
	},
	props: {
		configurable: !0,
		get: function() {
			var e = this;
			return { data: { get value() {
				return e.value;
			} } };
		}
	},
	__b: {
		configurable: !0,
		value: 1
	}
}), Y("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof U && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), Y("__r", function(e, t) {
	if (e(t), t.type !== D) {
		X();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return q(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				tt && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), X(n);
	}
}), Y("__e", function(e, t, n, r) {
	X(), e(t, n, r);
}), Y("diffed", function(e, t) {
	X();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = it(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function it(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = qe(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: q(function() {
			this.N = ct;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
Y("unmount", function(e, t) {
	if (typeof t.type == "string") {
		var n = t.__e;
		if (n) {
			var r = n.U;
			if (r) for (var i in n.U = void 0, r) {
				var a = r[i];
				a && a.d();
			}
		}
		var o = t.__np;
		if (o) {
			var s = t.props;
			for (var c in o) s[c] = o[c];
		}
		t.__np = void 0;
	} else {
		var l = t.__c;
		if (l) {
			var u = l.__$u;
			u && (l.__$u = void 0, u.d());
		}
	}
	e(t);
}), Y("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), O.prototype.shouldComponentUpdate = function(e, t) {
	if (this.__R) return !0;
	var n = this.__$u, r = n && n.s !== void 0;
	for (var i in t) return !0;
	if (this.__f || typeof this.u == "boolean" && !0 === this.u) {
		var a = 2 & this.__$f;
		if (!(r || a || 4 & this.__$f) || 1 & this.__$f) return !0;
	} else if (!(r || 4 & this.__$f) || 3 & this.__$f) return !0;
	for (var o in e) if (o !== "__source" && e[o] !== this.props[o]) return !0;
	for (var s in this.props) if (!(s in e)) return !0;
	return !1;
};
function at(e, t) {
	return Pe(function() {
		return qe(e, t);
	}, []);
}
var ot = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function st() {
	He(function() {
		for (var e; e = nt.shift();) et.call(e);
	});
}
function ct() {
	nt.push(this) === 1 && (o.requestAnimationFrame || ot)(st);
}
//#endregion
//#region src/state/quality-goals.ts
var lt = "/api/quality-goals?limit=200", ut = {
	data: null,
	error: ""
}, Z = qe(ut), dt = 0, ft = G(() => Z.value);
G(() => Z.value.data?.total ?? null);
function pt() {
	dt += 1, Z.value = ut;
}
async function mt(e) {
	let t = dt += 1;
	try {
		let n = await xe(lt, e);
		return t === dt && (Z.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === dt && (Z.value = {
			data: null,
			error: be(n)
		}), n;
	}
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var ht = 0;
Array.isArray;
function Q(e, t, n, r, i, a) {
	t ||= {};
	var s, c, l = t;
	if ("ref" in l) for (c in l = {}, t) c == "ref" ? s = t[c] : l[c] = t[c];
	var u = {
		type: e,
		props: l,
		key: n,
		ref: s,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: --ht,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (s = e.defaultProps)) for (c in s) l[c] === void 0 && (l[c] = s[c]);
	return o.vnode && o.vnode(u), u;
}
//#endregion
//#region src/islands/quality-goals.tsx
var gt = (e, t) => mt(t), _t = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function vt({ openItem: a, javTitleHtml: o, javDisplayName: s, srcBadge: c }) {
	let { data: l, error: u } = ft.value;
	if (u) return /* @__PURE__ */ Q("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: i(u, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let d = l?.items ?? [];
	return d.length ? /* @__PURE__ */ Q("div", {
		class: "qualitylist",
		children: d.map((r) => /* @__PURE__ */ Q("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ Q("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${s(r)}`,
				onClick: () => a(r.id),
				children: /* @__PURE__ */ Q("img", {
					src: _t(r),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ Q("div", { children: [
				/* @__PURE__ */ Q("h3", { children: /* @__PURE__ */ Q("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => a(r.id),
					dangerouslySetInnerHTML: { __html: o(r) }
				}) }),
				/* @__PURE__ */ Q("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ Q("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: c(r.location, r.cost) }
						}),
						/* @__PURE__ */ Q("span", { children: e[r.location] ?? r.location }),
						/* @__PURE__ */ Q("span", { children: t(r.duration) }),
						/* @__PURE__ */ Q("span", { children: n(r.size ?? 0) })
					]
				}),
				r.reason ? /* @__PURE__ */ Q("p", { children: r.reason }) : null
			] })]
		}, r.id))
	}) : /* @__PURE__ */ Q("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: r("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/state/index.ts
var yt = { "quality-goals": {
	refresh: mt,
	reset: pt
} }, bt = () => Object.keys(yt);
async function xt(e) {
	let t = yt[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/islands.ts
var St = { "quality-goals": {
	load: gt,
	component: vt
} }, Ct = () => Object.keys(St), $ = /* @__PURE__ */ new Map();
async function wt(e, t, n, r = {}) {
	let i = St[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	Tt(t);
	let a = {
		controller: new AbortController(),
		painted: !1
	};
	$.set(t, a);
	let o;
	try {
		o = {
			data: await i.load(n, a.controller.signal),
			error: ""
		};
	} catch (e) {
		if (a.controller.signal.aborted) return;
		o = {
			data: null,
			error: be(e)
		};
	}
	if ($.get(t) === a) {
		if (r.isCurrent && !r.isCurrent()) {
			$.delete(t);
			return;
		}
		t.textContent = "", a.painted = !0, _e(T(i.component, {
			...n,
			...o
		}), t);
	}
}
function Tt(e) {
	let t = $.get(e);
	t && (t.controller.abort(), $.delete(e), t.painted && _e(null, e));
}
//#endregion
export { Ct as islandNames, wt as mountIsland, xt as refreshStore, bt as storeNames, Tt as unmountIsland };
