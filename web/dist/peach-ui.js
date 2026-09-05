import { MEDIA_SOURCE_ICONS as e, emptyStateHtml as t, fieldsetTitle as n, noteHtml as r, selectFieldHtml as i, selectOptionIconHtml as a, setActionBusy as o, wireSelectField as s } from "/js/ui-components.js";
import { LOC as c, fmtDur as l, fmtSize as u } from "/js/core.js";
//#region node_modules/preact/dist/preact.module.js
var d, f, p, m, h, g, _, v, y, b, x, S, C, w, T, E = {}, D = [], O = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, k = Array.isArray;
function A(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function ee(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function te(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? d.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return j(e, o, r, i, null);
}
function j(e, t, n, r, i) {
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
		__v: i ?? ++p,
		__i: -1,
		__u: 0
	};
	return i == null && f.vnode != null && f.vnode(a), a;
}
function M(e) {
	return e.children;
}
function N(e, t) {
	this.props = e, this.context = t;
}
function P(e, t) {
	if (t == null) return e.__ ? P(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? P(e) : null;
}
function ne(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = A({}, t);
		a.__v = t.__v + 1, f.vnode && f.vnode(a), pe(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? P(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, he(r, a, i), t.__e = t.__ = null, a.__e != n && re(a);
	}
}
function re(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), re(e);
}
function ie(e) {
	(!e.__d && (e.__d = !0) && h.push(e) && !ae.__r++ || g != f.debounceRendering) && ((g = f.debounceRendering) || _)(ae);
}
function ae() {
	try {
		for (var e, t = 1; h.length;) h.length > t && h.sort(v), e = h.shift(), t = h.length, ne(e);
	} finally {
		h.length = ae.__r = 0;
	}
}
function oe(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || D, v = t.length;
	for (c = se(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || E, p.__i = d, g = pe(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && ve(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = ce(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function se(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = j(null, o, null, null, null) : k(o) ? o = e.__k[a] = j(M, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = j(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = le(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = P(s)), ye(s, s));
	return r;
}
function ce(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = ce(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = P(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function le(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function ue(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || O.test(t) ? n : n + "px";
}
function de(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || ue(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || ue(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(S, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[x] = r[x] : (n[x] = C, e.addEventListener(t, a ? T : w, a)) : e.removeEventListener(t, a ? T : w, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function fe(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[b] == null) t[b] = C++;
			else if (t[b] < n[x]) return;
			return n(f.event ? f.event(t) : t);
		}
	};
}
function pe(e, t, n, r, i, a, o, s, c, l) {
	var u, d, p, m, h, g, _, v, y, b, x, S, C, w, T, E, O = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (u = f.__b) && u(t);
	n: if (typeof O == "function") {
		d = o.length;
		try {
			if (y = t.props, b = O.prototype && O.prototype.render, x = (u = O.contextType) && r[u.__c], S = u ? x ? x.props.value : u.__ : r, n.__c ? v = (p = t.__c = n.__c).__ = p.__E : (b ? t.__c = p = new O(y, S) : (t.__c = p = new N(y, S), p.constructor = O, p.render = be), x && x.sub(p), p.state || (p.state = {}), p.__n = r, m = p.__d = !0, p.__h = [], p._sb = []), b && p.__s == null && (p.__s = p.state), b && O.getDerivedStateFromProps != null && (p.__s == p.state && (p.__s = A({}, p.__s)), A(p.__s, O.getDerivedStateFromProps(y, p.__s))), h = p.props, g = p.state, p.__v = t, m) b && O.getDerivedStateFromProps == null && p.componentWillMount != null && p.componentWillMount(), b && p.componentDidMount != null && p.__h.push(p.componentDidMount);
			else {
				if (b && O.getDerivedStateFromProps == null && y !== h && p.componentWillReceiveProps != null && p.componentWillReceiveProps(y, S), t.__v == n.__v || !p.__e && p.shouldComponentUpdate != null && !1 === p.shouldComponentUpdate(y, p.__s, S)) {
					t.__v != n.__v && (p.props = y, p.state = p.__s, p.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), D.push.apply(p.__h, p._sb), p._sb = [], p.__h.length && o.push(p), s = P(n);
					break n;
				}
				p.componentWillUpdate != null && p.componentWillUpdate(y, p.__s, S), b && p.componentDidUpdate != null && p.__h.push(function() {
					p.componentDidUpdate(h, g, _);
				});
			}
			if (p.context = S, p.props = y, p.__P = e, p.__e = !1, C = f.__r, w = 0, b) p.state = p.__s, p.__d = !1, C && C(t), u = p.render(p.props, p.state, p.context), D.push.apply(p.__h, p._sb), p._sb = [];
			else do
				p.__d = !1, C && C(t), u = p.render(p.props, p.state, p.context), p.state = p.__s;
			while (p.__d && ++w < 25);
			p.state = p.__s, p.getChildContext != null && (r = A(A({}, r), p.getChildContext())), b && !m && p.getSnapshotBeforeUpdate != null && (_ = p.getSnapshotBeforeUpdate(h, g)), T = u != null && u.type === M && u.key == null ? ge(u.props.children) : u, s = oe(e, k(T) ? T : [T], t, n, r, i, a, o, s, c, l), p.base = t.__e, t.__u &= -161, p.__h.length && o.push(p), v && (p.__E = p.__ = null);
		} catch (e) {
			if (o.length = d, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (E = a.length; E--;) ee(a[E]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || me(t), f.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = _e(n.__e, t, n, r, i, a, o, c, l);
	return (u = f.diffed) && u(t), 128 & t.__u ? void 0 : s;
}
function me(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(me));
}
function he(e, t, n) {
	for (var r = 0; r < n.length; r++) ve(n[r], n[++r], n[++r]);
	f.__c && f.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			f.__e(e, t.__v);
		}
	});
}
function ge(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : k(e) ? e.map(ge) : e.constructor === void 0 ? A({}, e) : null;
}
function _e(e, t, n, r, i, a, o, s, c) {
	var l, u, p, m, h, g, _, v = n.props || E, y = t.props, b = t.type;
	if (b == "svg" ? i = "http://www.w3.org/2000/svg" : b == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (l = 0; l < a.length; l++) if ((h = a[l]) && "setAttribute" in h == !!b && (b ? h.localName == b : h.nodeType == 3)) {
			e = h, a[l] = null;
			break;
		}
	}
	if (e == null) {
		if (b == null) return document.createTextNode(y);
		e = document.createElementNS(i, b, y.is && y), s &&= (f.__m && f.__m(t, a), !1), a = null;
	}
	if (b == null) v === y || s && e.data == y || (e.data = y);
	else {
		if (a = b == "textarea" && y.defaultValue != null ? null : a && d.call(e.childNodes), !s && a != null) for (v = {}, l = 0; l < e.attributes.length; l++) v[(h = e.attributes[l]).name] = h.value;
		for (l in v) h = v[l], l == "dangerouslySetInnerHTML" ? p = h : l == "children" || l in y || l == "value" && "defaultValue" in y || l == "checked" && "defaultChecked" in y || de(e, l, null, h, i);
		for (l in y) h = y[l], l == "children" ? m = h : l == "dangerouslySetInnerHTML" ? u = h : l == "value" ? g = h : l == "checked" ? _ = h : s && typeof h != "function" || v[l] === h || de(e, l, h, v[l], i);
		if (u) s || p && (u.__html == p.__html || u.__html == e.innerHTML) || (e.innerHTML = u.__html), t.__k = [];
		else if (p && (e.innerHTML = ""), oe(t.type == "template" ? e.content : e, k(m) ? m : [m], t, n, r, b == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && P(n, 0), s, c), a != null) for (l = a.length; l--;) ee(a[l]);
		s && b != "textarea" || (l = "value", b == "progress" && g == null ? e.removeAttribute("value") : g != null && (g !== e[l] || b == "progress" && !g || b == "option" && g != v[l]) && de(e, l, g, v[l], i), l = "checked", _ != null && _ != e[l] && de(e, l, _, v[l], i));
	}
	return e;
}
function ve(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		f.__e(e, n);
	}
}
function ye(e, t, n) {
	var r, i;
	if (f.unmount && f.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || ve(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			f.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && ye(r[i], t, n || typeof e.type != "function");
	n || ee(e.__e), e.__c = e.__ = e.__e = void 0;
}
function be(e, t, n) {
	return this.constructor(e, n);
}
function xe(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), f.__ && f.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], pe(t, e = (!r && n || t).__k = te(M, null, [e]), i || E, E, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? d.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), he(a, e, o), e.props.children = null;
}
d = D.slice, f = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, p = 0, m = function(e) {
	return e != null && e.constructor === void 0;
}, N.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = A({}, this.state);
	typeof e == "function" && (e = e(A({}, n), this.props)), e && A(n, e), e != null && this.__v && (t && this._sb.push(t), ie(this));
}, N.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), ie(this));
}, N.prototype.render = M, h = [], _ = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, v = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, ae.__r = 0, y = Math.random().toString(8), b = "__d" + y, x = "__a" + y, S = /(PointerCapture)$|Capture$/i, C = 0, w = fe(!1), T = fe(!0);
//#endregion
//#region src/api.ts
var Se = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(e), this.name = "ApiError", this.status = t, this.body = n;
	}
}, Ce = (e) => {
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
}, F = (e) => e instanceof Error ? e.message : String(e);
async function I(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new Se(Ce(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function we(e, t, n = "POST", r) {
	let i = await fetch(e, {
		method: n,
		...r ? { signal: r } : {},
		headers: {
			Accept: "application/json",
			"Content-Type": "application/json"
		},
		credentials: "same-origin",
		body: JSON.stringify(t)
	}), a = null;
	try {
		a = await i.json();
	} catch {}
	if (!i.ok) throw new Se(Ce(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var L, R, Te, Ee, De = 0, Oe = [], z = f, ke = z.__b, Ae = z.__r, je = z.diffed, Me = z.__c, Ne = z.unmount, Pe = z.__;
function Fe(e, t) {
	z.__h && z.__h(R, e, De || t), De = 0;
	var n = R.__H || (R.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function B(e) {
	return De = 1, Ie(Ge, e);
}
function Ie(e, t, n) {
	var r = Fe(L++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : Ge(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = R, !R.__f)) {
		var i = function(e, t, n) {
			if (!r.__c.__H) return !0;
			var i = !1, o = r.__c.props !== e;
			if (r.__c.__H.__.some(function(e) {
				if (e.__N) {
					i = !0;
					var t = e.__[0];
					e.__ = e.__N, e.__N = void 0, t !== e.__[0] && (o = !0);
				}
			}), a) {
				var s = a.call(this, e, t, n);
				return i ? s || o : s;
			}
			return !i || o;
		};
		R.__f = !0;
		var a = R.shouldComponentUpdate, o = R.componentWillUpdate;
		R.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, R.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function Le(e, t) {
	var n = Fe(L++, 3);
	!z.__s && We(n.__H, t) && (n.__ = e, n.u = t, R.__H.__h.push(n));
}
function V(e, t) {
	var n = Fe(L++, 4);
	!z.__s && We(n.__H, t) && (n.__ = e, n.u = t, R.__h.push(n));
}
function H(e) {
	return De = 5, Re(function() {
		return { current: e };
	}, []);
}
function Re(e, t) {
	var n = Fe(L++, 7);
	return We(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function ze() {
	for (var e; e = Oe.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(He), t.__h.some(Ue), t.__h = [];
		} catch (n) {
			t.__h = [], z.__e(n, e.__v);
		}
	}
}
z.__b = function(e) {
	R = null, ke && ke(e);
}, z.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Pe && Pe(e, t);
}, z.__r = function(e) {
	Ae && Ae(e), L = 0;
	var t = (R = e.__c).__H;
	t && (Te === R ? (t.__h = [], R.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(He), t.__h.some(Ue), t.__h = [], L = 0)), Te = R;
}, z.diffed = function(e) {
	je && je(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (Oe.push(t) !== 1 && Ee === z.requestAnimationFrame || ((Ee = z.requestAnimationFrame) || Ve)(ze)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), Te = R = null;
}, z.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(He), e.__h = e.__h.filter(function(e) {
				return !e.__ || Ue(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], z.__e(n, e.__v);
		}
	}), Me && Me(e, t);
}, z.unmount = function(e) {
	Ne && Ne(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			He(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && z.__e(t, n.__v));
};
var Be = typeof requestAnimationFrame == "function";
function Ve(e) {
	var t, n = function() {
		clearTimeout(r), Be && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Be && (t = requestAnimationFrame(n));
}
function He(e) {
	var t = R, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), R = t;
}
function Ue(e) {
	var t = R;
	e.__c = e.__(), R = t;
}
function We(e, t) {
	return !e || e.length !== t.length || t.some(function(t, n) {
		return t !== e[n];
	});
}
function Ge(e, t) {
	return typeof t == "function" ? t(e) : t;
}
//#endregion
//#region node_modules/preact/jsx-runtime/dist/jsxRuntime.module.js
var Ke = 0;
Array.isArray;
function U(e, t, n, r, i, a) {
	t ||= {};
	var o, s, c = t;
	if ("ref" in c) for (s in c = {}, t) s == "ref" ? o = t[s] : c[s] = t[s];
	var l = {
		type: e,
		props: c,
		key: n,
		ref: o,
		__k: null,
		__: null,
		__b: 0,
		__e: null,
		__c: null,
		constructor: void 0,
		__v: --Ke,
		__i: -1,
		__u: 0,
		__source: i,
		__self: a
	};
	if (typeof e == "function" && (o = e.defaultProps)) for (s in o) c[s] === void 0 && (c[s] = o[s]);
	return f.vnode && f.vnode(l), l;
}
//#endregion
//#region src/islands/configuration.tsx
var qe = "/api/configuration", Je = "/api/pick-folder", Ye = 8e3, Xe = (e, t) => I(qe, t), W = ({ html: e, class: t }) => /* @__PURE__ */ U("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), Ze = (e) => !(e instanceof Se) || e.status !== 400 ? null : e.body?.errors ?? null;
function Qe({ facts: e }) {
	return /* @__PURE__ */ U("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ U("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ U(W, { html: n("configFactsTitle", "运行信息") }), /* @__PURE__ */ U("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ U(M, { children: [/* @__PURE__ */ U("dt", { children: e.term }), /* @__PURE__ */ U("dd", { children: e.value })] }))
			})]
		})
	});
}
function $e({ data: t }) {
	let [r, i] = B(t.media_sources), [s, c] = B(""), l = H(null);
	Le(() => () => l.current?.abort(), []);
	let u = async (e) => {
		if (l.current) return;
		let t = new AbortController();
		l.current = t, o(e, !0), c("");
		try {
			let e = await I(qe, t.signal);
			t.signal.aborted || i(e.media_sources);
		} catch (e) {
			t.signal.aborted || c(F(e));
		} finally {
			l.current = null, o(e, !1);
		}
	};
	return r ? /* @__PURE__ */ U("section", {
		class: "configfieldset",
		"aria-labelledby": "configMountsTitle",
		children: /* @__PURE__ */ U("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ U(W, { html: n("configMountsTitle", "挂载状态") }),
				/* @__PURE__ */ U("dl", {
					class: "configfacts",
					children: r.map((t) => /* @__PURE__ */ U(M, { children: [/* @__PURE__ */ U("dt", { children: [/* @__PURE__ */ U("span", {
						"aria-hidden": "true",
						dangerouslySetInnerHTML: { __html: a(e[t.location]) }
					}), {
						local: "本地磁盘",
						115: "CloudDrive · 115",
						pikpak: "CloudDrive · PikPak"
					}[t.location] || t.location] }), /* @__PURE__ */ U("dd", { children: [
						t.path || "未配置挂载点",
						" ",
						/* @__PURE__ */ U("span", {
							class: `configstatus ${t.online === !0 ? "online" : t.online === !1 ? "offline" : "unknown"}`,
							children: t.online === !0 ? "在线" : t.online === !1 ? "离线" : "未检测"
						})
					] })] }))
				}),
				s ? /* @__PURE__ */ U("p", {
					class: "configbad",
					role: "alert",
					children: s
				}) : null,
				/* @__PURE__ */ U("button", {
					type: "button",
					class: "geist-button",
					onClick: (e) => u(e.currentTarget),
					children: "刷新挂载状态"
				})
			]
		})
	}) : null;
}
function et({ value: t, label: n, onChange: r }) {
	let a = H(null), o = H(null), c = H(r);
	return c.current = r, V(() => {
		let r = a.current;
		r.innerHTML = i([
			["local", "本地磁盘"],
			["115", "CloudDrive · 115"],
			["pikpak", "CloudDrive · PikPak"]
		].map(([t, n]) => [
			t,
			n,
			e[t]
		]), t, { label: n });
		let l = s(r.firstElementChild);
		o.current = l;
		let u = () => c.current(l.value);
		return l.addEventListener("change", u), () => {
			o.current = null, l.disabled = !0, l.removeEventListener("change", u), r.replaceChildren();
		};
	}, [n]), V(() => {
		o.current && (o.current.value = t);
	}, [t]), /* @__PURE__ */ U("div", {
		ref: a,
		class: "configsourcecontrol"
	});
}
function tt({ data: e, receipt: t }) {
	let i = e.media_sources?.filter((e) => [
		"local",
		"115",
		"pikpak"
	].includes(e.location)), [a, s] = B(i?.length ? i.map((e) => e.path) : e.media_dirs.length ? e.media_dirs : [""]), [c, l] = B(i?.map((e) => e.location) ?? []), [u, d] = B(i?.map((e) => e.root) ?? []), [f, p] = B(String(e.port)), [m, h] = B(!1), [g, _] = B([]), [v, y] = B(""), [b, x] = B(""), [S, C] = B(null), [w, T] = B(null), E = H(!1), D = H(e.revision), O = H([]), k = H(null);
	V(() => {
		w !== null && (O.current[w]?.focus(), T(null));
	}, [w]), Le(() => {
		if (!S) return;
		let e = setTimeout(() => location.assign(S.url), Ye);
		return () => clearTimeout(e);
	}, [S]);
	let A = (e, t) => {
		s((n) => n.map((n, r) => r === e ? t : n));
	}, ee = () => {
		T(a.length), s((e) => [...e, ""]);
	}, te = (e) => {
		l((t) => t.filter((t, n) => n !== e)), d((t) => t.filter((t, n) => n !== e)), s((t) => t.filter((t, n) => n !== e)), _((t) => t.filter((t, n) => n !== e));
	}, j = (e, t) => {
		_((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, M = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			o(t, !0);
			try {
				let { path: t } = await we(Je, { initial: a[e] ?? "" });
				t && (A(e, t), j(e, ""));
			} catch (t) {
				j(e, F(t));
			} finally {
				o(t, !1);
			}
		}
	};
	return S ? /* @__PURE__ */ U("div", {
		class: "configsaved",
		role: "status",
		children: [/* @__PURE__ */ U(W, { html: r("配置已保存，Peach 正在重新启动。", {
			variant: "success",
			label: "已保存"
		}) }), /* @__PURE__ */ U("p", {
			class: "confighelp",
			children: [
				"几秒后自动打开新地址；没跳转就点 ",
				/* @__PURE__ */ U("a", {
					href: S.url,
					children: "进入馆藏"
				}),
				"。"
			]
		})]
	}) : /* @__PURE__ */ U("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (n) => {
			if (n.preventDefault(), !E.current) {
				E.current = !0, o(k.current, !0), x("");
				try {
					let n = await we(qe, {
						revision: D.current,
						media_dirs: a,
						...e.media_sources ? { media_sources: a.map((e, t) => ({
							path: e,
							location: c[t] || "local",
							root: u[t] || ""
						})) } : {},
						port: f,
						scan_now: m
					});
					D.current = n.revision, _([]), y(""), t("已保存配置"), C(n);
				} catch (e) {
					let t = Ze(e);
					t ? (_(t.media_dirs ?? []), y(t.port ?? "")) : (_([]), y(""), x(F(e)));
				} finally {
					E.current = !1, o(k.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ U("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ U(W, { html: n("configTitle", "这台电脑") }),
				/* @__PURE__ */ U("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ U("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ U("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: a.map((t, n) => /* @__PURE__ */ U("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ U("span", {
										class: "configpathlabel",
										children: ["本机文件夹 ", n + 1]
									}),
									/* @__PURE__ */ U("input", {
										class: "geist-input",
										type: "text",
										value: t,
										"aria-label": `媒体文件夹 ${n + 1}`,
										"aria-invalid": g[n] ? "true" : void 0,
										onInput: (e) => A(n, e.currentTarget.value),
										ref: (e) => {
											O.current[n] = e;
										}
									}),
									/* @__PURE__ */ U("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => M(n, e.currentTarget),
										children: /* @__PURE__ */ U("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ U("use", { href: "#i-folder-search" })
										})
									}),
									a.length > 1 ? /* @__PURE__ */ U("button", {
										type: "button",
										class: "geist-button configrm",
										"aria-label": "移除这个文件夹",
										onClick: () => te(n),
										children: /* @__PURE__ */ U("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ U("use", { href: "#i-x" })
										})
									}) : null,
									/* @__PURE__ */ U("div", {
										class: "configsource",
										children: [/* @__PURE__ */ U("div", {
											class: "configsourcelabel",
											children: ["媒体来源", /* @__PURE__ */ U(et, {
												label: `媒体来源 ${n + 1}`,
												value: c[n] || "local",
												onChange: (e) => {
													let t = [...c];
													t[n] = e, l(t);
												}
											})]
										}), e.windows === !1 ? /* @__PURE__ */ U("label", { children: ["Windows 中的对应路径", /* @__PURE__ */ U("input", {
											class: "geist-input",
											"aria-label": `Windows 中的对应路径 ${n + 1}`,
											value: u[n] || "",
											placeholder: "例如 B:\\\\",
											onInput: (e) => {
												let t = [...u];
												t[n] = e.currentTarget.value, d(t);
											}
										})] }) : null]
									}),
									g[n] ? /* @__PURE__ */ U("p", {
										class: "configbad",
										role: "alert",
										children: g[n]
									}) : null
								]
							}, n))
						}),
						/* @__PURE__ */ U("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: ee,
							children: "添加文件夹"
						}),
						c.some((e) => e === "115" || e === "pikpak") ? /* @__PURE__ */ U("p", {
							class: "confighelp",
							children: ["先在 CloudDrive 登录网盘并完成挂载。", /* @__PURE__ */ U("a", {
								href: "https://www.clouddrive2.com/help.html",
								target: "_blank",
								rel: "noreferrer",
								children: ["挂载帮助", /* @__PURE__ */ U("svg", {
									"aria-hidden": "true",
									viewBox: "0 0 24 24",
									children: /* @__PURE__ */ U("use", { href: "#i-external-link" })
								})]
							})]
						}) : null,
						e.windows === !1 ? /* @__PURE__ */ U("p", {
							class: "confighelp",
							children: "本机文件夹是这台电脑读取媒体的位置。Windows 中的对应路径用于匹配馆藏中已有的路径，例如 B:\\ 对应本机挂载文件夹。"
						}) : null
					]
				}),
				/* @__PURE__ */ U("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ U("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ U("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: f,
							"aria-invalid": v ? "true" : void 0,
							onInput: (e) => p(e.currentTarget.value)
						}),
						v ? /* @__PURE__ */ U("p", {
							class: "configbad",
							role: "alert",
							children: v
						}) : null,
						/* @__PURE__ */ U("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ U("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ U("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ U("input", {
							type: "checkbox",
							checked: m,
							onChange: (e) => h(e.currentTarget.checked)
						}), /* @__PURE__ */ U("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ U("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ U("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ U("span", { children: "保存后扫描媒体文件夹" })]
				}),
				b ? /* @__PURE__ */ U(W, { html: r(b, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ U("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ U("p", { children: "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ U("button", {
				type: "submit",
				class: "geist-button primary",
				ref: k,
				children: "保存配置"
			})]
		})]
	});
}
function nt({ receipt: e, data: t, error: n }) {
	return n || !t ? /* @__PURE__ */ U(W, {
		class: "configpage",
		html: r(n || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ U("div", {
		class: "configpage",
		children: [
			t.editable ? /* @__PURE__ */ U(tt, {
				data: t,
				receipt: e
			}) : /* @__PURE__ */ U(W, { html: r(t.notice, {
				variant: "secondary",
				label: "只读"
			}) }),
			/* @__PURE__ */ U(Qe, { facts: t.facts }),
			/* @__PURE__ */ U($e, { data: t })
		]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var rt = Symbol.for("preact-signals");
function it() {
	if (J > 1) J--;
	else {
		var e, t = !1;
		for ((function() {
			var e = ut;
			for (ut = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); q !== void 0;) {
			var n = q;
			for (q = void 0, st++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && mt(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (st = 0, J--, t) throw e;
	}
}
function at(e) {
	if (J > 0) return e();
	lt = ++ct, J++;
	try {
		return e();
	} finally {
		it();
	}
}
var G, K = void 0;
function ot(e) {
	var t = K, n = G;
	K = void 0, G = void 0;
	try {
		return e();
	} finally {
		K = t, G = n;
	}
}
var q = void 0, J = 0, st = 0, ct = 0, lt = 0, ut = void 0, dt = 0;
function ft(e) {
	if (K !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== K) return t = {
			i: 0,
			S: e,
			p: K.s,
			n: void 0,
			t: K,
			e: void 0,
			x: void 0,
			r: t
		}, K.s !== void 0 && (K.s.n = t), K.s = t, e.n = t, 32 & K.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = K.s, t.n = void 0, K.s.n = t, K.s = t), t;
	}
}
function Y(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
Y.prototype.brand = rt, Y.prototype.h = function() {
	return !0;
}, Y.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? ot(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, Y.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && ot(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, Y.prototype.subscribe = function(e) {
	var t = this;
	return xt(function() {
		var n = t.value;
		ot(function() {
			return e(n);
		});
	}, { name: "sub" });
}, Y.prototype.valueOf = function() {
	return this.value;
}, Y.prototype.toString = function() {
	return this.value + "";
}, Y.prototype.toJSON = function() {
	return this.value;
}, Y.prototype.peek = function() {
	var e = this;
	return ot(function() {
		return e.value;
	});
}, Object.defineProperty(Y.prototype, "value", {
	get: function() {
		var e = ft(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (st > 100) throw Error("Cycle detected");
			(function(e) {
				J !== 0 && st === 0 && e.l !== lt && (e.l = lt, ut = {
					S: e,
					v: e.v,
					i: e.i,
					o: ut
				});
			})(this), this.v = e, this.i++, dt++, J++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				it();
			}
		}
	}
});
function pt(e, t) {
	return new Y(e, t);
}
function mt(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function ht(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function gt(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function X(e, t) {
	Y.call(this, void 0, t), this.x = e, this.s = void 0, this.g = dt - 1, this.f = 4;
}
X.prototype = new Y(), X.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === dt)) return !0;
	if (this.g = dt, this.f |= 1, this.i > 0 && !mt(this)) return this.f &= -2, !0;
	var e = K;
	try {
		ht(this), K = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return K = e, gt(this), this.f &= -2, !0;
}, X.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	Y.prototype.S.call(this, e);
}, X.prototype.U = function(e) {
	if (this.t !== void 0 && (Y.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, X.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(X.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = ft(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function _t(e, t) {
	return new X(e, t);
}
function vt(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		J++;
		var n = K;
		K = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, yt(e), t;
		} finally {
			K = n, it();
		}
	}
}
function yt(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, vt(e);
}
function bt(e) {
	if (K !== this) throw Error("Out-of-order effect");
	gt(this), K = e, this.f &= -2, 8 & this.f && yt(this), it();
}
function Z(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, G && G.push(this);
}
Z.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, Z.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, vt(this), ht(this), J++;
	var e = K;
	return K = this, bt.bind(this, e);
}, Z.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = q, q = this);
}, Z.prototype.d = function() {
	this.f |= 8, 1 & this.f || yt(this);
}, Z.prototype.dispose = function() {
	this.d();
};
function xt(e, t) {
	var n = new Z(e, t);
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
var St, Ct, wt = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, Tt = [];
xt(function() {
	St = this.N;
})();
function Q(e, t) {
	f[e] = t.bind(null, f[e] || function() {});
}
function Et(e) {
	if (Ct) {
		var t = Ct;
		Ct = void 0, t();
	}
	Ct = e && e.S();
}
function Dt(e) {
	var t = this, n = e.data, r = kt(n);
	r.name = "ReactiveDom", r.value = n;
	var i = Re(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = _t(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = _t(function() {
			return !Array.isArray(i.value) && !m(i.value);
		}), o = xt(function() {
			if (this.N = Mt, a.value) {
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
Dt.displayName = "ReactiveTextNode", Object.defineProperties(Y.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: Dt
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
}), Q("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof Y && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), Q("__r", function(e, t) {
	if (e(t), t.type !== M) {
		Et();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return xt(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				wt && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), Et(n);
	}
}), Q("__e", function(e, t, n, r) {
	Et(), e(t, n, r);
}), Q("diffed", function(e, t) {
	Et();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = Ot(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function Ot(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = pt(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: xt(function() {
			this.N = Mt;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
Q("unmount", function(e, t) {
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
}), Q("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), N.prototype.shouldComponentUpdate = function(e, t) {
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
function kt(e, t) {
	return Re(function() {
		return pt(e, t);
	}, []);
}
var At = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function jt() {
	at(function() {
		for (var e; e = Tt.shift();) St.call(e);
	});
}
function Mt() {
	Tt.push(this) === 1 && (f.requestAnimationFrame || At)(jt);
}
//#endregion
//#region src/state/quality-goals.ts
var Nt = "/api/quality-goals?limit=200", Pt = {
	data: null,
	error: ""
}, Ft = pt(Pt), It = 0, Lt = _t(() => Ft.value);
_t(() => Ft.value.data?.total ?? null);
function Rt() {
	It += 1, Ft.value = Pt;
}
async function zt(e) {
	let t = It += 1;
	try {
		let n = await I(Nt, e);
		return t === It && (Ft.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === It && (Ft.value = {
			data: null,
			error: F(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var Bt = (e, t) => zt(t), Vt = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function Ht({ openItem: e, javTitleHtml: n, javDisplayName: i, srcBadge: a }) {
	let { data: o, error: s } = Lt.value;
	if (s) return /* @__PURE__ */ U("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: r(s, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let d = o?.items ?? [];
	return d.length ? /* @__PURE__ */ U("div", {
		class: "qualitylist",
		children: d.map((t) => /* @__PURE__ */ U("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ U("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${i(t)}`,
				onClick: () => e(t.id),
				children: /* @__PURE__ */ U("img", {
					src: Vt(t),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ U("div", { children: [
				/* @__PURE__ */ U("h3", { children: /* @__PURE__ */ U("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => e(t.id),
					dangerouslySetInnerHTML: { __html: n(t) }
				}) }),
				/* @__PURE__ */ U("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ U("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: a(t.location, t.cost) }
						}),
						/* @__PURE__ */ U("span", { children: c[t.location] ?? t.location }),
						/* @__PURE__ */ U("span", { children: l(t.duration) }),
						/* @__PURE__ */ U("span", { children: u(t.size ?? 0) })
					]
				}),
				t.reason ? /* @__PURE__ */ U("p", { children: t.reason }) : null
			] })]
		}, t.id))
	}) : /* @__PURE__ */ U("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: t("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function Ut(e) {
	let t = e.pause || ((e) => new Promise((t) => setTimeout(t, e))), n = 0;
	for (; e.active();) {
		let r;
		try {
			r = await e.read(AbortSignal.timeout(15e3));
		} catch (r) {
			if (!e.active()) return;
			n++, e.disconnected(r), await t(Math.min(2e3 * 2 ** Math.min(n, 4), 3e4));
			continue;
		}
		if (!e.active() || (n = 0, e.render(r), e.once) || !e.keepWatching && r.status !== "running") return;
		await t(2e3);
	}
}
function Wt(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	Ut({
		read: e.read,
		active: () => !i && e.active() && t.isConnected,
		keepWatching: e.watchIdle !== !1,
		render: (a) => {
			let o = a.status === "running";
			if (e.host.hidden = !o, e.busy(o), o) {
				r = a.job_id, r && sessionStorage.setItem(n, r);
				let i = a.current, o = (i?.attempt || 1) > 1 ? ` · 第 ${i?.attempt}/${i?.max_attempts} 次尝试${i?.retry_in ? `，${i.retry_in} 秒后重试` : ""}` : "", s = (e.title || (a.total ? `${a.older ? "抓取历史" : "检查更新"}：已完成 ${a.checked || 0}/${a.total} 个来源` : "正在准备检查任务…")) + (i ? ` · ${i.label || i.provider || ""}${o}` : ""), c = e.loading(s) + ((a.total || 0) > 0 ? e.progress(a.checked || 0, a.total) : "");
				t.innerHTML = e.container ? e.container(c) : c;
			} else if (r && r === a.job_id) r = void 0, i = !0, e.host.hidden = a.status !== "failed", sessionStorage.removeItem(n), t.innerHTML = a.status === "failed" ? e.note(a.error || "检查失败") : "", e.complete(a);
			else {
				if (r && a.status === "idle") {
					e.host.hidden = !1, t.innerHTML = e.note("任务状态已失效，请重新发起任务"), sessionStorage.removeItem(n), i = !0;
					return;
				}
				t.innerHTML = "";
			}
		},
		disconnected: () => {
			e.host.hidden = !1, t.innerHTML = e.note("暂时无法读取进度，正在重新连接…");
		}
	});
}
//#endregion
//#region src/islands/scraping.tsx
var Gt = (e, t) => I("/api/scraping", t);
function Kt({ value: e, onChange: t }) {
	let n = H(null), r = H(t);
	return r.current = t, V(() => {
		let t = n.current;
		t.innerHTML = i([
			["environment", "系统代理"],
			["direct", "应用直连"],
			["proxy", "自定义代理"]
		], e, { label: "连接方式" });
		let a = s(t.firstElementChild), o = () => r.current(a.value);
		return a.addEventListener("change", o), () => {
			a.disabled = !0, a.removeEventListener("change", o), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ U("div", {
		ref: n,
		class: "scraping-network"
	});
}
function qt({ source: e, toast: t }) {
	let [i, a] = B(e), [s, c] = B(e.network), [l, u] = B(""), [d, f] = B(""), [p, m] = B(""), [h, g] = B("paste"), [_, v] = B(""), [y, b] = B(!1), [x, S] = B(""), [C, w] = B([]), T = H(null), E = H(null);
	V(() => {
		E.current?.querySelectorAll("footer button").forEach((e) => o(e, y));
	}, [y]);
	let D = H(new AbortController());
	Le(() => () => D.current.abort(), []);
	async function O(n) {
		if (!y) {
			b(!0), S(""), w([]);
			try {
				if (n === "check") {
					let t = await we("/api/scraping/check", { source: e.source }, "POST", D.current.signal);
					D.current.signal.aborted || w(t.results);
				} else {
					let r = await we("/api/scraping/settings", {
						source: e.source,
						network: s,
						proxy: l,
						cookie: d,
						cookies_text: p,
						revoke: n === "revoke"
					}, "POST", D.current.signal);
					D.current.signal.aborted || (a(r.saved), u(""), f(""), m(""), v(""), T.current && (T.current.value = ""), t(n === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				D.current.signal.aborted || S(F(e));
			} finally {
				D.current.signal.aborted || b(!1);
			}
		}
	}
	return /* @__PURE__ */ U("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ U("form", {
			ref: E,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), O("save");
			},
			children: [/* @__PURE__ */ U("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ U("div", { dangerouslySetInnerHTML: { __html: n(`scraping-${e.source}`, e.label) } }),
					/* @__PURE__ */ U("a", {
						class: "scraping-url",
						href: e.login,
						target: "_blank",
						rel: "noopener noreferrer",
						children: e.login
					}),
					/* @__PURE__ */ U("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ U(Kt, {
							value: s,
							onChange: c
						})]
					}),
					s === "proxy" && /* @__PURE__ */ U("label", { children: ["代理地址", /* @__PURE__ */ U("input", {
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: l,
						placeholder: i.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						disabled: y,
						onInput: (e) => u(e.currentTarget.value)
					})] }),
					e.accepts_cookie && /* @__PURE__ */ U(M, { children: [
						/* @__PURE__ */ U("p", { children: i.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ U("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ U("label", { children: [/* @__PURE__ */ U("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: h === t,
								onChange: () => {
									g(t), f(""), m(""), v("");
								}
							}), /* @__PURE__ */ U("span", { children: n })] }, t))
						}),
						h === "paste" ? /* @__PURE__ */ U("label", { children: ["Cookie", /* @__PURE__ */ U("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: d,
							disabled: y,
							onInput: (e) => f(e.currentTarget.value)
						})] }) : /* @__PURE__ */ U("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ U("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ U("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ U("span", {
										class: "scraping-file-name",
										children: _ || "未选择文件"
									}),
									/* @__PURE__ */ U("input", {
										ref: T,
										type: "file",
										accept: ".txt",
										disabled: y,
										onChange: async (e) => {
											let t = e.currentTarget.files?.[0];
											if (!t) {
												m(""), v("");
												return;
											}
											if (m(""), t.size > 262144) {
												S("Cookie 文本超过 256 KiB"), e.currentTarget.value = "";
												return;
											}
											b(!0);
											try {
												let e = await t.text();
												D.current.signal.aborted || (m(e), v(t.name));
											} catch {
												D.current.signal.aborted || S("Cookie 文件未读取，请重新选择");
											} finally {
												D.current.signal.aborted || b(!1);
											}
										}
									})
								]
							})]
						})
					] }),
					x && /* @__PURE__ */ U("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: r(x, { variant: "error" }) }
					}),
					C.map((t) => /* @__PURE__ */ U("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: r(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ U("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					/* @__PURE__ */ U("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					}),
					/* @__PURE__ */ U("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void O("check"),
						children: "检查连接"
					}),
					e.accepts_cookie && i.cookie_saved && /* @__PURE__ */ U("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void O("revoke"),
						children: "撤销 Cookie"
					})
				]
			})]
		})
	});
}
function Jt({ data: e, error: t, toast: i }) {
	let [a, s] = B(""), [c, l] = B(!1), [u, d] = B(""), f = H(null);
	V(() => o(f.current, c), [c]);
	let p = H(new AbortController()), m = H(0);
	async function h(e = !1) {
		let t = ++m.current;
		await Ut({
			read: (e) => I("/api/scraping/cover", e),
			active: () => !p.current.signal.aborted && t === m.current,
			render: (t) => {
				l(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && d(t.error || "采集未取得"), t.status === "complete" && !e && i(t.result || "封面采集完成");
			},
			disconnected: () => d("连接中断，正在重新读取后台进度")
		});
	}
	Le(() => (h(!0), () => p.current.abort()), []);
	async function g() {
		if (!c) {
			m.current++, l(!0), d("");
			try {
				await we("/api/scraping/cover", { code: a }, "POST", p.current.signal), await h();
			} catch (e) {
				p.current.signal.aborted || (l(!1), d(F(e)));
			}
		}
	}
	return t ? /* @__PURE__ */ U("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: r(t, { variant: "error" }) }
	}) : /* @__PURE__ */ U("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ U("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ U("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ U("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ U("div", { dangerouslySetInnerHTML: { __html: n("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ U("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), g();
							},
							children: [/* @__PURE__ */ U("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: a,
								disabled: c,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => s(e.currentTarget.value)
							}), /* @__PURE__ */ U("button", {
								ref: f,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						u && /* @__PURE__ */ U("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: r(u, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ U(qt, {
				source: e,
				toast: i
			}, e.source))
		]
	});
}
//#endregion
//#region src/state/index.ts
var Yt = { "quality-goals": {
	refresh: zt,
	reset: Rt
} }, Xt = () => Object.keys(Yt);
async function Zt(e) {
	let t = Yt[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/sidebar.ts
function Qt(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function $t(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function en(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/islands.ts
var tn = {
	scraping: {
		load: Gt,
		component: Jt
	},
	"quality-goals": {
		load: Bt,
		component: Ht
	},
	configuration: {
		load: Xe,
		component: nt
	}
}, nn = () => Object.keys(tn), $ = /* @__PURE__ */ new Map();
async function rn(e, t, n, r = {}) {
	let i = tn[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	an(t);
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
			error: F(e)
		};
	}
	if ($.get(t) !== a) return;
	if (r.isCurrent && !r.isCurrent()) {
		$.delete(t);
		return;
	}
	t.textContent = "", a.painted = !0;
	let s = {
		...n,
		...o
	};
	xe(te(i.component, s), t);
}
function an(e) {
	let t = $.get(e);
	t && (t.controller.abort(), $.delete(e), t.painted && xe(null, e));
}
//#endregion
export { Wt as followJobProgress, nn as islandNames, rn as mountIsland, Zt as refreshStore, Qt as sidebarHasCatalogContent, en as sidebarTagCounts, Xt as storeNames, $t as syncSidebarSurface, an as unmountIsland, Ut as watchJob };
