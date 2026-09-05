import { emptyStateHtml as e, fieldsetTitle as t, noteHtml as n, selectFieldHtml as r, setActionBusy as i, wireSelectField as a } from "/js/ui-components.js";
import { LOC as o, fmtDur as s, fmtSize as c } from "/js/core.js";
//#region node_modules/preact/dist/preact.module.js
var l, u, d, f, p, m, h, g, _, v, y, b, x, S, C, w = {}, T = [], E = /acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i, D = Array.isArray;
function O(e, t) {
	for (var n in t) e[n] = t[n];
	return e;
}
function ee(e) {
	e && e.parentNode && e.parentNode.removeChild(e);
}
function k(e, t, n) {
	var r, i, a, o = {};
	for (a in t) a == "key" ? r = t[a] : a == "ref" ? i = t[a] : o[a] = t[a];
	if (arguments.length > 2 && (o.children = arguments.length > 3 ? l.call(arguments, 2) : n), typeof e == "function" && e.defaultProps != null) for (a in e.defaultProps) o[a] === void 0 && (o[a] = e.defaultProps[a]);
	return A(e, o, r, i, null);
}
function A(e, t, n, r, i) {
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
		__v: i ?? ++d,
		__i: -1,
		__u: 0
	};
	return i == null && u.vnode != null && u.vnode(a), a;
}
function j(e) {
	return e.children;
}
function M(e, t) {
	this.props = e, this.context = t;
}
function N(e, t) {
	if (t == null) return e.__ ? N(e.__, e.__i + 1) : null;
	for (var n; t < e.__k.length; t++) if ((n = e.__k[t]) != null && n.__e != null) return n.__e;
	return typeof e.type == "function" ? N(e) : null;
}
function te(e) {
	if (e.__P && e.__d) {
		var t = e.__v, n = t.__e, r = [], i = [], a = O({}, t);
		a.__v = t.__v + 1, u.vnode && u.vnode(a), fe(e.__P, a, t, e.__n, e.__P.namespaceURI, 32 & t.__u ? [n] : null, r, n ?? N(t), !!(32 & t.__u), i), a.__v = t.__v, a.__.__k[a.__i] = a, me(r, a, i), t.__e = t.__ = null, a.__e != n && ne(a);
	}
}
function ne(e) {
	if ((e = e.__) != null && e.__c != null) return e.__e = e.__c.base = null, e.__k.some(function(t) {
		if (t != null && t.__e != null) return e.__e = e.__c.base = t.__e;
	}), ne(e);
}
function re(e) {
	(!e.__d && (e.__d = !0) && p.push(e) && !ie.__r++ || m != u.debounceRendering) && ((m = u.debounceRendering) || h)(ie);
}
function ie() {
	try {
		for (var e, t = 1; p.length;) p.length > t && p.sort(g), e = p.shift(), t = p.length, te(e);
	} finally {
		p.length = ie.__r = 0;
	}
}
function ae(e, t, n, r, i, a, o, s, c, l, u) {
	var d, f, p, m, h, g, _ = r && r.__k || T, v = t.length;
	for (c = oe(n, t, _, c, v), d = 0; d < v; d++) (p = n.__k[d]) != null && (f = p.__i != -1 && _[p.__i] || w, p.__i = d, g = fe(e, p, f, i, a, o, s, c, l, u), m = p.__e, p.ref && f.ref != p.ref && (f.ref && _e(f.ref, null, p), u.push(p.ref, p.__c || m, p)), h == null && m != null && (h = m), 4 & p.__u ? (c = se(p, c, e), f.__e && (f.__e = null)) : typeof p.type == "function" && g !== void 0 ? c = g : m && (c = m.nextSibling), p.__u &= -7);
	return n.__e = h, c;
}
function oe(e, t, n, r, i) {
	var a, o, s, c, l, u = n.length, d = u, f = 0;
	for (e.__k = Array(i), a = 0; a < i; a++) (o = t[a]) != null && typeof o != "boolean" && typeof o != "function" ? (typeof o == "string" || typeof o == "number" || typeof o == "bigint" || o.constructor == String ? o = e.__k[a] = A(null, o, null, null, null) : D(o) ? o = e.__k[a] = A(j, { children: o }, null, null, null) : o.constructor === void 0 && o.__b > 0 ? o = e.__k[a] = A(o.type, o.props, o.key, o.ref ? o.ref : null, o.__v) : e.__k[a] = o, c = a + f, o.__ = e, o.__b = e.__b + 1, s = null, (l = o.__i = ce(o, n, c, d)) != -1 && (d--, (s = n[l]) && (s.__u |= 2)), s == null || s.__v == null ? (l == -1 && (i > u ? f-- : i < u && f++), typeof o.type != "function" && (o.__u |= 4)) : l != c && (l == c - 1 ? f-- : l == c + 1 ? f++ : (l > c ? f-- : f++, o.__u |= 4))) : e.__k[a] = null;
	if (d) for (a = 0; a < u; a++) (s = n[a]) != null && !(2 & s.__u) && (s.__e == r && (r = N(s)), ve(s, s));
	return r;
}
function se(e, t, n) {
	var r, i;
	if (typeof e.type == "function") {
		for (r = e.__k, i = 0; r && i < r.length; i++) r[i] && (r[i].__ = e, t = se(r[i], t, n));
		return t;
	}
	e.__e != t && (t && e.type && !t.parentNode && (t = N(e)), t = n.insertBefore(e.__e, t || null));
	do
		t &&= t.nextSibling;
	while (t != null && t.nodeType == 8);
	return t;
}
function ce(e, t, n, r) {
	var i, a, o, s = e.key, c = e.type, l = t[n], u = l != null && !(2 & l.__u);
	if (l === null && s == null || u && s == l.key && c == l.type) return n;
	if (r > +!!u) {
		for (i = n - 1, a = n + 1; i >= 0 || a < t.length;) if ((l = t[o = i >= 0 ? i-- : a++]) != null && !(2 & l.__u) && s == l.key && c == l.type) return o;
	}
	return -1;
}
function le(e, t, n) {
	t[0] == "-" ? e.setProperty(t, n ?? "") : e[t] = n == null ? "" : typeof n != "number" || E.test(t) ? n : n + "px";
}
function ue(e, t, n, r, i) {
	var a, o;
	n: if (t == "style") {
		if (typeof n == "string") e.style.cssText = n;
		else {
			if (typeof r == "string" && (e.style.cssText = r = ""), r) for (t in r) n && t in n || le(e.style, t, "");
			if (n) for (t in n) r && n[t] == r[t] || le(e.style, t, n[t]);
		}
	} else if (t[0] == "o" && t[1] == "n") a = t != (t = t.replace(b, "$1")), o = t.toLowerCase(), t = o in e || t == "onFocusOut" || t == "onFocusIn" ? o.slice(2) : t.slice(2), e.l ||= {}, e.l[t + a] = n, n ? r ? n[y] = r[y] : (n[y] = x, e.addEventListener(t, a ? C : S, a)) : e.removeEventListener(t, a ? C : S, a);
	else {
		if (i == "http://www.w3.org/2000/svg") t = t.replace(/xlink(H|:h)/, "h").replace(/sName$/, "s");
		else if (t != "width" && t != "height" && t != "href" && t != "list" && t != "form" && t != "tabIndex" && t != "download" && t != "rowSpan" && t != "colSpan" && t != "role" && t != "popover" && t in e) try {
			e[t] = n ?? "";
			break n;
		} catch {}
		typeof n == "function" || (n == null || !1 === n && t[4] != "-" ? e.removeAttribute(t) : e.setAttribute(t, t == "popover" && n == 1 ? "" : n));
	}
}
function de(e) {
	return function(t) {
		if (this.l) {
			var n = this.l[t.type + e];
			if (t[v] == null) t[v] = x++;
			else if (t[v] < n[y]) return;
			return n(u.event ? u.event(t) : t);
		}
	};
}
function fe(e, t, n, r, i, a, o, s, c, l) {
	var d, f, p, m, h, g, _, v, y, b, x, S, C, w, E, k, A = t.type;
	if (t.constructor !== void 0) return null;
	128 & n.__u && (c = !!(32 & n.__u), a = [s = t.__e = n.__e]), (d = u.__b) && d(t);
	n: if (typeof A == "function") {
		f = o.length;
		try {
			if (y = t.props, b = A.prototype && A.prototype.render, x = (d = A.contextType) && r[d.__c], S = d ? x ? x.props.value : d.__ : r, n.__c ? v = (p = t.__c = n.__c).__ = p.__E : (b ? t.__c = p = new A(y, S) : (t.__c = p = new M(y, S), p.constructor = A, p.render = ye), x && x.sub(p), p.state || (p.state = {}), p.__n = r, m = p.__d = !0, p.__h = [], p._sb = []), b && p.__s == null && (p.__s = p.state), b && A.getDerivedStateFromProps != null && (p.__s == p.state && (p.__s = O({}, p.__s)), O(p.__s, A.getDerivedStateFromProps(y, p.__s))), h = p.props, g = p.state, p.__v = t, m) b && A.getDerivedStateFromProps == null && p.componentWillMount != null && p.componentWillMount(), b && p.componentDidMount != null && p.__h.push(p.componentDidMount);
			else {
				if (b && A.getDerivedStateFromProps == null && y !== h && p.componentWillReceiveProps != null && p.componentWillReceiveProps(y, S), t.__v == n.__v || !p.__e && p.shouldComponentUpdate != null && !1 === p.shouldComponentUpdate(y, p.__s, S)) {
					t.__v != n.__v && (p.props = y, p.state = p.__s, p.__d = !1), t.__e = n.__e, t.__k = n.__k, t.__k.some(function(e) {
						e && (e.__ = t);
					}), T.push.apply(p.__h, p._sb), p._sb = [], p.__h.length && o.push(p), s = N(n);
					break n;
				}
				p.componentWillUpdate != null && p.componentWillUpdate(y, p.__s, S), b && p.componentDidUpdate != null && p.__h.push(function() {
					p.componentDidUpdate(h, g, _);
				});
			}
			if (p.context = S, p.props = y, p.__P = e, p.__e = !1, C = u.__r, w = 0, b) p.state = p.__s, p.__d = !1, C && C(t), d = p.render(p.props, p.state, p.context), T.push.apply(p.__h, p._sb), p._sb = [];
			else do
				p.__d = !1, C && C(t), d = p.render(p.props, p.state, p.context), p.state = p.__s;
			while (p.__d && ++w < 25);
			p.state = p.__s, p.getChildContext != null && (r = O(O({}, r), p.getChildContext())), b && !m && p.getSnapshotBeforeUpdate != null && (_ = p.getSnapshotBeforeUpdate(h, g)), E = d != null && d.type === j && d.key == null ? he(d.props.children) : d, s = ae(e, D(E) ? E : [E], t, n, r, i, a, o, s, c, l), p.base = t.__e, t.__u &= -161, p.__h.length && o.push(p), v && (p.__E = p.__ = null);
		} catch (e) {
			if (o.length = f, t.__v = null, c || a != null) {
				if (e.then) {
					for (t.__u |= c ? 160 : 128; s && s.nodeType == 8 && s.nextSibling;) s = s.nextSibling;
					a != null && (a[a.indexOf(s)] = null), t.__e = s;
				} else if (a != null) for (k = a.length; k--;) ee(a[k]);
			} else t.__e = n.__e;
			t.__k ??= n.__k || [], e.then || pe(t), u.__e(e, t, n);
		}
	} else a == null && t.__v == n.__v ? (t.__k = n.__k, t.__e = n.__e) : s = t.__e = ge(n.__e, t, n, r, i, a, o, c, l);
	return (d = u.diffed) && d(t), 128 & t.__u ? void 0 : s;
}
function pe(e) {
	e && (e.__c && (e.__c.__e = !0), e.__k && e.__k.some(pe));
}
function me(e, t, n) {
	for (var r = 0; r < n.length; r++) _e(n[r], n[++r], n[++r]);
	u.__c && u.__c(t, e), e.some(function(t) {
		try {
			e = t.__h, t.__h = [], e.some(function(e) {
				e.call(t);
			});
		} catch (e) {
			u.__e(e, t.__v);
		}
	});
}
function he(e) {
	return typeof e != "object" || !e || e.__b > 0 ? e : D(e) ? e.map(he) : e.constructor === void 0 ? O({}, e) : null;
}
function ge(e, t, n, r, i, a, o, s, c) {
	var d, f, p, m, h, g, _, v = n.props || w, y = t.props, b = t.type;
	if (b == "svg" ? i = "http://www.w3.org/2000/svg" : b == "math" ? i = "http://www.w3.org/1998/Math/MathML" : i ||= "http://www.w3.org/1999/xhtml", a != null) {
		for (d = 0; d < a.length; d++) if ((h = a[d]) && "setAttribute" in h == !!b && (b ? h.localName == b : h.nodeType == 3)) {
			e = h, a[d] = null;
			break;
		}
	}
	if (e == null) {
		if (b == null) return document.createTextNode(y);
		e = document.createElementNS(i, b, y.is && y), s &&= (u.__m && u.__m(t, a), !1), a = null;
	}
	if (b == null) v === y || s && e.data == y || (e.data = y);
	else {
		if (a = b == "textarea" && y.defaultValue != null ? null : a && l.call(e.childNodes), !s && a != null) for (v = {}, d = 0; d < e.attributes.length; d++) v[(h = e.attributes[d]).name] = h.value;
		for (d in v) h = v[d], d == "dangerouslySetInnerHTML" ? p = h : d == "children" || d in y || d == "value" && "defaultValue" in y || d == "checked" && "defaultChecked" in y || ue(e, d, null, h, i);
		for (d in y) h = y[d], d == "children" ? m = h : d == "dangerouslySetInnerHTML" ? f = h : d == "value" ? g = h : d == "checked" ? _ = h : s && typeof h != "function" || v[d] === h || ue(e, d, h, v[d], i);
		if (f) s || p && (f.__html == p.__html || f.__html == e.innerHTML) || (e.innerHTML = f.__html), t.__k = [];
		else if (p && (e.innerHTML = ""), ae(t.type == "template" ? e.content : e, D(m) ? m : [m], t, n, r, b == "foreignObject" ? "http://www.w3.org/1999/xhtml" : i, a, o, a ? a[0] : n.__k && N(n, 0), s, c), a != null) for (d = a.length; d--;) ee(a[d]);
		s && b != "textarea" || (d = "value", b == "progress" && g == null ? e.removeAttribute("value") : g != null && (g !== e[d] || b == "progress" && !g || b == "option" && g != v[d]) && ue(e, d, g, v[d], i), d = "checked", _ != null && _ != e[d] && ue(e, d, _, v[d], i));
	}
	return e;
}
function _e(e, t, n) {
	try {
		if (typeof e == "function") {
			var r = typeof e.__u == "function";
			r && e.__u(), r && t == null || (e.__u = e(t));
		} else e.current = t;
	} catch (e) {
		u.__e(e, n);
	}
}
function ve(e, t, n) {
	var r, i;
	if (u.unmount && u.unmount(e), (r = e.ref) && (r.current && r.current != e.__e || _e(r, null, t)), (r = e.__c) != null) {
		if (r.componentWillUnmount) try {
			r.componentWillUnmount();
		} catch (e) {
			u.__e(e, t);
		}
		r.base = r.__P = r.__n = null;
	}
	if (r = e.__k) for (i = 0; i < r.length; i++) r[i] && ve(r[i], t, n || typeof e.type != "function");
	n || ee(e.__e), e.__c = e.__ = e.__e = void 0;
}
function ye(e, t, n) {
	return this.constructor(e, n);
}
function be(e, t, n) {
	var r, i, a, o;
	t == document && (t = document.documentElement), u.__ && u.__(e, t), i = (r = typeof n == "function") ? null : n && n.__k || t.__k, a = [], o = [], fe(t, e = (!r && n || t).__k = k(j, null, [e]), i || w, w, t.namespaceURI, !r && n ? [n] : i ? null : t.firstChild ? l.call(t.childNodes) : null, a, !r && n ? n : i ? i.__e : t.firstChild, r, o), me(a, e, o), e.props.children = null;
}
l = T.slice, u = { __e: function(e, t, n, r) {
	for (var i, a, o; t = t.__;) if ((i = t.__c) && !i.__) try {
		if ((a = i.constructor) && a.getDerivedStateFromError != null && (i.setState(a.getDerivedStateFromError(e)), o = i.__d), i.componentDidCatch != null && (i.componentDidCatch(e, r || {}), o = i.__d), o) return i.__E = i;
	} catch (t) {
		e = t;
	}
	throw e;
} }, d = 0, f = function(e) {
	return e != null && e.constructor === void 0;
}, M.prototype.setState = function(e, t) {
	var n = this.__s != null && this.__s != this.state ? this.__s : this.__s = O({}, this.state);
	typeof e == "function" && (e = e(O({}, n), this.props)), e && O(n, e), e != null && this.__v && (t && this._sb.push(t), re(this));
}, M.prototype.forceUpdate = function(e) {
	this.__v && (this.__e = !0, e && this.__h.push(e), re(this));
}, M.prototype.render = j, p = [], h = typeof Promise == "function" ? Promise.prototype.then.bind(Promise.resolve()) : setTimeout, g = function(e, t) {
	return e.__v.__b - t.__v.__b;
}, ie.__r = 0, _ = Math.random().toString(8), v = "__d" + _, y = "__a" + _, b = /(PointerCapture)$|Capture$/i, x = 0, S = de(!1), C = de(!0);
//#endregion
//#region src/api.ts
var xe = class extends Error {
	status;
	body;
	constructor(e, t, n = null) {
		super(e), this.name = "ApiError", this.status = t, this.body = n;
	}
}, Se = (e) => {
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
}, P = (e) => e instanceof Error ? e.message : String(e);
async function Ce(e, t) {
	let n = await fetch(e, {
		headers: { Accept: "application/json" },
		credentials: "same-origin",
		...t ? { signal: t } : {}
	}), r = null;
	try {
		r = await n.json();
	} catch {}
	if (!n.ok) throw new xe(Se(r) || `请求失败（${n.status}）`, n.status);
	return r;
}
async function F(e, t, n = "POST", r) {
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
	if (!i.ok) throw new xe(Se(a) || `请求失败（${i.status}）`, i.status, a);
	return a;
}
//#endregion
//#region node_modules/preact/hooks/dist/hooks.module.js
var I, L, we, Te, Ee = 0, De = [], R = u, Oe = R.__b, ke = R.__r, Ae = R.diffed, je = R.__c, Me = R.unmount, Ne = R.__;
function Pe(e, t) {
	R.__h && R.__h(L, e, Ee || t), Ee = 0;
	var n = L.__H || (L.__H = {
		__: [],
		__h: []
	});
	return e >= n.__.length && n.__.push({}), n.__[e];
}
function z(e) {
	return Ee = 1, Fe(Ge, e);
}
function Fe(e, t, n) {
	var r = Pe(I++, 2);
	if (r.t = e, !r.__c && (r.__ = [n ? n(t) : Ge(void 0, t), function(e) {
		var t = r.__N ? r.__N[0] : r.__[0], n = r.t(t, e);
		t !== n && (r.__N = [n, r.__[1]], r.__c.setState({}));
	}], r.__c = L, !L.__f)) {
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
		L.__f = !0;
		var a = L.shouldComponentUpdate, o = L.componentWillUpdate;
		L.componentWillUpdate = function(e, t, n) {
			if (this.__e) {
				var r = a;
				a = void 0, i(e, t, n), a = r;
			}
			o && o.call(this, e, t, n);
		}, L.shouldComponentUpdate = i;
	}
	return r.__N || r.__;
}
function Ie(e, t) {
	var n = Pe(I++, 3);
	!R.__s && We(n.__H, t) && (n.__ = e, n.u = t, L.__H.__h.push(n));
}
function Le(e, t) {
	var n = Pe(I++, 4);
	!R.__s && We(n.__H, t) && (n.__ = e, n.u = t, L.__h.push(n));
}
function B(e) {
	return Ee = 5, Re(function() {
		return { current: e };
	}, []);
}
function Re(e, t) {
	var n = Pe(I++, 7);
	return We(n.__H, t) && (n.__ = e(), n.__H = t, n.__h = e), n.__;
}
function ze() {
	for (var e; e = De.shift();) {
		var t = e.__H;
		if (e.__P && t) try {
			t.__h.some(He), t.__h.some(Ue), t.__h = [];
		} catch (n) {
			t.__h = [], R.__e(n, e.__v);
		}
	}
}
R.__b = function(e) {
	L = null, Oe && Oe(e);
}, R.__ = function(e, t) {
	e && t.__k && t.__k.__m && (e.__m = t.__k.__m), Ne && Ne(e, t);
}, R.__r = function(e) {
	ke && ke(e), I = 0;
	var t = (L = e.__c).__H;
	t && (we === L ? (t.__h = [], L.__h = [], t.__.some(function(e) {
		e.__N && (e.__ = e.__N), e.u = e.__N = void 0;
	})) : (t.__h.some(He), t.__h.some(Ue), t.__h = [], I = 0)), we = L;
}, R.diffed = function(e) {
	Ae && Ae(e);
	var t = e.__c;
	t && t.__H && (t.__H.__h.length && (De.push(t) !== 1 && Te === R.requestAnimationFrame || ((Te = R.requestAnimationFrame) || Ve)(ze)), t.__H.__.some(function(e) {
		e.u &&= (e.__H = e.u, void 0);
	})), we = L = null;
}, R.__c = function(e, t) {
	t.some(function(e) {
		try {
			e.__h.some(He), e.__h = e.__h.filter(function(e) {
				return !e.__ || Ue(e);
			});
		} catch (n) {
			t.some(function(e) {
				e.__h &&= [];
			}), t = [], R.__e(n, e.__v);
		}
	}), je && je(e, t);
}, R.unmount = function(e) {
	Me && Me(e);
	var t, n = e.__c;
	n && n.__H && (n.__H.__.some(function(e) {
		try {
			He(e);
		} catch (e) {
			t = e;
		}
	}), n.__H = void 0, t && R.__e(t, n.__v));
};
var Be = typeof requestAnimationFrame == "function";
function Ve(e) {
	var t, n = function() {
		clearTimeout(r), Be && cancelAnimationFrame(t), setTimeout(e);
	}, r = setTimeout(n, 35);
	Be && (t = requestAnimationFrame(n));
}
function He(e) {
	var t = L, n = e.__c;
	typeof n == "function" && (e.__c = void 0, n()), L = t;
}
function Ue(e) {
	var t = L;
	e.__c = e.__(), L = t;
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
function V(e, t, n, r, i, a) {
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
	return u.vnode && u.vnode(l), l;
}
//#endregion
//#region src/islands/configuration.tsx
var qe = "/api/configuration", Je = "/api/pick-folder", Ye = 8e3, Xe = (e, t) => Ce(qe, t), H = ({ html: e, class: t }) => /* @__PURE__ */ V("div", {
	class: t,
	dangerouslySetInnerHTML: { __html: e }
}), Ze = (e) => !(e instanceof xe) || e.status !== 400 ? null : e.body?.errors ?? null;
function Qe({ facts: e }) {
	return /* @__PURE__ */ V("section", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configFactsTitle",
		children: /* @__PURE__ */ V("div", {
			class: "geist-fieldset-content",
			children: [/* @__PURE__ */ V(H, { html: t("configFactsTitle", "运行信息") }), /* @__PURE__ */ V("dl", {
				class: "configfacts",
				children: e.map((e) => /* @__PURE__ */ V(j, { children: [/* @__PURE__ */ V("dt", { children: e.term }), /* @__PURE__ */ V("dd", { children: e.value })] }))
			})]
		})
	});
}
function $e({ data: e, receipt: r }) {
	let [a, o] = z(e.media_dirs.length ? e.media_dirs : [""]), [s, c] = z(String(e.port)), [l, u] = z(!1), [d, f] = z([]), [p, m] = z(""), [h, g] = z(""), [_, v] = z(null), [y, b] = z(null), x = B(!1), S = B(e.revision), C = B([]), w = B(null);
	Le(() => {
		y !== null && (C.current[y]?.focus(), b(null));
	}, [y]), Ie(() => {
		if (!_) return;
		let e = setTimeout(() => location.assign(_.url), Ye);
		return () => clearTimeout(e);
	}, [_]);
	let T = (e, t) => {
		o((n) => n.map((n, r) => r === e ? t : n));
	}, E = () => {
		b(a.length), o((e) => [...e, ""]);
	}, D = (e) => {
		o((t) => t.filter((t, n) => n !== e)), f((t) => t.filter((t, n) => n !== e));
	}, O = (e, t) => {
		f((n) => {
			let r = [...n];
			for (; r.length <= e;) r.push("");
			return r[e] = t, r;
		});
	}, ee = async (e, t) => {
		if (t.getAttribute("aria-busy") !== "true") {
			i(t, !0);
			try {
				let { path: t } = await F(Je, { initial: a[e] ?? "" });
				t && (T(e, t), O(e, ""));
			} catch (t) {
				O(e, P(t));
			} finally {
				i(t, !1);
			}
		}
	};
	return _ ? /* @__PURE__ */ V("div", {
		class: "configsaved",
		role: "status",
		children: [/* @__PURE__ */ V(H, { html: n("配置已保存，Peach 正在重新启动。", {
			variant: "success",
			label: "已保存"
		}) }), /* @__PURE__ */ V("p", {
			class: "confighelp",
			children: [
				"几秒后自动打开新地址；没跳转就点 ",
				/* @__PURE__ */ V("a", {
					href: _.url,
					children: "进入馆藏"
				}),
				"。"
			]
		})]
	}) : /* @__PURE__ */ V("form", {
		class: "configfieldset",
		"data-geist-fieldset": !0,
		"aria-labelledby": "configTitle",
		onSubmit: async (e) => {
			if (e.preventDefault(), !x.current) {
				x.current = !0, i(w.current, !0), g("");
				try {
					let e = await F(qe, {
						revision: S.current,
						media_dirs: a,
						port: s,
						scan_now: l
					});
					S.current = e.revision, f([]), m(""), r("已保存配置"), v(e);
				} catch (e) {
					let t = Ze(e);
					t ? (f(t.media_dirs ?? []), m(t.port ?? "")) : (f([]), m(""), g(P(e)));
				} finally {
					x.current = !1, i(w.current, !1);
				}
			}
		},
		noValidate: !0,
		children: [/* @__PURE__ */ V("div", {
			class: "geist-fieldset-content",
			children: [
				/* @__PURE__ */ V(H, { html: t("configTitle", "这台电脑") }),
				/* @__PURE__ */ V("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ V("span", {
							class: "configlabel",
							id: "configDirsLabel",
							children: "媒体文件夹"
						}),
						/* @__PURE__ */ V("div", {
							class: "configdirs",
							role: "group",
							"aria-labelledby": "configDirsLabel",
							children: a.map((e, t) => /* @__PURE__ */ V("div", {
								class: "configdir",
								children: [
									/* @__PURE__ */ V("input", {
										class: "geist-input",
										type: "text",
										value: e,
										"aria-label": `媒体文件夹 ${t + 1}`,
										"aria-invalid": d[t] ? "true" : void 0,
										onInput: (e) => T(t, e.currentTarget.value),
										ref: (e) => {
											C.current[t] = e;
										}
									}),
									/* @__PURE__ */ V("button", {
										type: "button",
										class: "geist-button configpick",
										"aria-label": "选择文件夹",
										onClick: (e) => ee(t, e.currentTarget),
										children: /* @__PURE__ */ V("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ V("use", { href: "#i-folder-search" })
										})
									}),
									a.length > 1 ? /* @__PURE__ */ V("button", {
										type: "button",
										class: "geist-button configrm",
										"aria-label": "移除这个文件夹",
										onClick: () => D(t),
										children: /* @__PURE__ */ V("svg", {
											viewBox: "0 0 24 24",
											"aria-hidden": "true",
											children: /* @__PURE__ */ V("use", { href: "#i-x" })
										})
									}) : null,
									d[t] ? /* @__PURE__ */ V("p", {
										class: "configbad",
										role: "alert",
										children: d[t]
									}) : null
								]
							}, t))
						}),
						/* @__PURE__ */ V("button", {
							type: "button",
							class: "geist-button configadd",
							onClick: E,
							children: "添加文件夹"
						}),
						/* @__PURE__ */ V("p", {
							class: "confighelp",
							children: "Peach 从这些文件夹读取视频和图片。可以是外置硬盘上的文件夹，但必须已经存在。"
						})
					]
				}),
				/* @__PURE__ */ V("div", {
					class: "configfield",
					children: [
						/* @__PURE__ */ V("label", {
							for: "configPort",
							children: "本机访问端口"
						}),
						/* @__PURE__ */ V("input", {
							id: "configPort",
							class: "geist-input",
							type: "text",
							inputMode: "numeric",
							value: s,
							"aria-invalid": p ? "true" : void 0,
							onInput: (e) => c(e.currentTarget.value)
						}),
						p ? /* @__PURE__ */ V("p", {
							class: "configbad",
							role: "alert",
							children: p
						}) : null,
						/* @__PURE__ */ V("p", {
							class: "confighelp",
							children: "浏览器地址里冒号后面的数字，一般不用改。"
						})
					]
				}),
				/* @__PURE__ */ V("label", {
					class: "configcheck",
					children: [/* @__PURE__ */ V("span", {
						class: "pcheck",
						children: [/* @__PURE__ */ V("input", {
							type: "checkbox",
							checked: l,
							onChange: (e) => u(e.currentTarget.checked)
						}), /* @__PURE__ */ V("span", {
							"aria-hidden": "true",
							children: /* @__PURE__ */ V("svg", {
								viewBox: "0 0 24 24",
								children: /* @__PURE__ */ V("use", { href: "#i-check" })
							})
						})]
					}), /* @__PURE__ */ V("span", { children: "保存后扫描媒体文件夹" })]
				}),
				h ? /* @__PURE__ */ V(H, { html: n(h, {
					variant: "error",
					label: "没有保存"
				}) }) : null
			]
		}), /* @__PURE__ */ V("div", {
			class: "geist-fieldset-footer",
			"data-geist-fieldset-footer": !0,
			children: [/* @__PURE__ */ V("p", { children: "保存后 Peach 会重新启动，端口改了就用新地址打开。" }), /* @__PURE__ */ V("button", {
				type: "submit",
				class: "geist-button primary",
				ref: w,
				children: "保存配置"
			})]
		})]
	});
}
function et({ receipt: e, data: t, error: r }) {
	return r || !t ? /* @__PURE__ */ V(H, {
		class: "configpage",
		html: n(r || "没有读到配置", {
			variant: "error",
			label: "打不开配置"
		})
	}) : /* @__PURE__ */ V("div", {
		class: "configpage",
		children: [t.editable ? /* @__PURE__ */ V($e, {
			data: t,
			receipt: e
		}) : /* @__PURE__ */ V(H, { html: n(t.notice, {
			variant: "secondary",
			label: "只读"
		}) }), /* @__PURE__ */ V(Qe, { facts: t.facts })]
	});
}
//#endregion
//#region node_modules/@preact/signals-core/dist/signals-core.module.js
var tt = Symbol.for("preact-signals");
function nt() {
	if (K > 1) K--;
	else {
		var e, t = !1;
		for ((function() {
			var e = ct;
			for (ct = void 0; e !== void 0;) {
				var t = e.S;
				if (t.v === e.v) for (var n = t.t; n !== void 0; n = n.x) n.i === e.i && (n.i = t.i);
				e = e.o;
			}
		})(); G !== void 0;) {
			var n = G;
			for (G = void 0, at++; n !== void 0;) {
				var r = n.u;
				if (n.u = void 0, n.f &= -3, !(8 & n.f) && ft(n)) try {
					n.c();
				} catch (n) {
					t ||= (e = n, !0);
				}
				n = r;
			}
		}
		if (at = 0, K--, t) throw e;
	}
}
function rt(e) {
	if (K > 0) return e();
	st = ++ot, K++;
	try {
		return e();
	} finally {
		nt();
	}
}
var U, W = void 0;
function it(e) {
	var t = W, n = U;
	W = void 0, U = void 0;
	try {
		return e();
	} finally {
		W = t, U = n;
	}
}
var G = void 0, K = 0, at = 0, ot = 0, st = 0, ct = void 0, lt = 0;
function ut(e) {
	if (W !== void 0) {
		var t = e.n;
		if (t === void 0 || t.t !== W) return t = {
			i: 0,
			S: e,
			p: W.s,
			n: void 0,
			t: W,
			e: void 0,
			x: void 0,
			r: t
		}, W.s !== void 0 && (W.s.n = t), W.s = t, e.n = t, 32 & W.f && e.S(t), t;
		if (t.i === -1) return t.i = 0, t.n !== void 0 && (t.n.p = t.p, t.p !== void 0 && (t.p.n = t.n), t.p = W.s, t.n = void 0, W.s.n = t, W.s = t), t;
	}
}
function q(e, t) {
	this.v = e, this.i = 0, this.n = void 0, this.t = void 0, this.l = 0, this.W = t?.watched, this.Z = t?.unwatched, this.name = t?.name;
}
q.prototype.brand = tt, q.prototype.h = function() {
	return !0;
}, q.prototype.S = function(e) {
	var t = this, n = this.t;
	n !== e && e.e === void 0 && (e.x = n, this.t = e, n === void 0 ? it(function() {
		var e;
		(e = t.W) == null || e.call(t);
	}) : n.e = e);
}, q.prototype.U = function(e) {
	var t = this;
	if (this.t !== void 0) {
		var n = e.e, r = e.x;
		n !== void 0 && (n.x = r, e.e = void 0), r !== void 0 && (r.e = n, e.x = void 0), e === this.t && (this.t = r, r === void 0 && it(function() {
			var e;
			(e = t.Z) == null || e.call(t);
		}));
	}
}, q.prototype.subscribe = function(e) {
	var t = this;
	return X(function() {
		var n = t.value;
		it(function() {
			return e(n);
		});
	}, { name: "sub" });
}, q.prototype.valueOf = function() {
	return this.value;
}, q.prototype.toString = function() {
	return this.value + "";
}, q.prototype.toJSON = function() {
	return this.value;
}, q.prototype.peek = function() {
	var e = this;
	return it(function() {
		return e.value;
	});
}, Object.defineProperty(q.prototype, "value", {
	get: function() {
		var e = ut(this);
		return e !== void 0 && (e.i = this.i), this.v;
	},
	set: function(e) {
		if (e !== this.v) {
			if (at > 100) throw Error("Cycle detected");
			(function(e) {
				K !== 0 && at === 0 && e.l !== st && (e.l = st, ct = {
					S: e,
					v: e.v,
					i: e.i,
					o: ct
				});
			})(this), this.v = e, this.i++, lt++, K++;
			try {
				for (var t = this.t; t !== void 0; t = t.x) t.t.N();
			} finally {
				nt();
			}
		}
	}
});
function dt(e, t) {
	return new q(e, t);
}
function ft(e) {
	for (var t = e.s; t !== void 0; t = t.n) if (t.S.i !== t.i || !t.S.h() || t.S.i !== t.i) return !0;
	return !1;
}
function pt(e) {
	for (var t = e.s; t !== void 0; t = t.n) {
		var n = t.S.n;
		if (n !== void 0 && (t.r = n), t.S.n = t, t.i = -1, t.n === void 0) {
			e.s = t;
			break;
		}
	}
}
function mt(e) {
	for (var t = e.s, n = void 0; t !== void 0;) {
		var r = t.p;
		t.i === -1 ? (t.S.U(t), r !== void 0 && (r.n = t.n), t.n !== void 0 && (t.n.p = r)) : n = t, t.S.n = t.r, t.r !== void 0 && (t.r = void 0), t = r;
	}
	e.s = n;
}
function J(e, t) {
	q.call(this, void 0, t), this.x = e, this.s = void 0, this.g = lt - 1, this.f = 4;
}
J.prototype = new q(), J.prototype.h = function() {
	if (this.f &= -3, 1 & this.f) return !1;
	if ((36 & this.f) == 32 || (this.f &= -5, this.g === lt)) return !0;
	if (this.g = lt, this.f |= 1, this.i > 0 && !ft(this)) return this.f &= -2, !0;
	var e = W;
	try {
		pt(this), W = this;
		var t = this.x();
		(16 & this.f || this.v !== t || this.i === 0) && (this.v = t, this.f &= -17, this.i++);
	} catch (e) {
		this.v = e, this.f |= 16, this.i++;
	}
	return W = e, mt(this), this.f &= -2, !0;
}, J.prototype.S = function(e) {
	if (this.t === void 0) {
		this.f |= 36;
		for (var t = this.s; t !== void 0; t = t.n) t.S.S(t);
	}
	q.prototype.S.call(this, e);
}, J.prototype.U = function(e) {
	if (this.t !== void 0 && (q.prototype.U.call(this, e), this.t === void 0)) {
		this.f &= -33;
		for (var t = this.s; t !== void 0; t = t.n) t.S.U(t);
	}
}, J.prototype.N = function() {
	if (!(2 & this.f)) {
		this.f |= 6;
		for (var e = this.t; e !== void 0; e = e.x) e.t.N();
	}
}, Object.defineProperty(J.prototype, "value", { get: function() {
	if (1 & this.f) throw Error("Cycle detected");
	var e = ut(this);
	if (this.h(), e !== void 0 && (e.i = this.i), 16 & this.f) throw this.v;
	return this.v;
} });
function ht(e, t) {
	return new J(e, t);
}
function gt(e) {
	var t = e.m;
	if (e.m = void 0, typeof t == "function") {
		K++;
		var n = W;
		W = void 0;
		try {
			t();
		} catch (t) {
			throw e.f &= -2, e.f |= 8, _t(e), t;
		} finally {
			W = n, nt();
		}
	}
}
function _t(e) {
	for (var t = e.s; t !== void 0; t = t.n) t.S.U(t);
	e.x = void 0, e.s = void 0, gt(e);
}
function vt(e) {
	if (W !== this) throw Error("Out-of-order effect");
	mt(this), W = e, this.f &= -2, 8 & this.f && _t(this), nt();
}
function Y(e, t) {
	this.x = e, this.m = void 0, this.s = void 0, this.u = void 0, this.f = 32, this.name = t?.name, U && U.push(this);
}
Y.prototype.c = function() {
	var e = this.S();
	try {
		if (8 & this.f || this.x === void 0) return;
		var t = this.x();
		typeof t == "function" && (this.m = t);
	} finally {
		e();
	}
}, Y.prototype.S = function() {
	if (1 & this.f) throw Error("Cycle detected");
	this.f |= 1, this.f &= -9, gt(this), pt(this), K++;
	var e = W;
	return W = this, vt.bind(this, e);
}, Y.prototype.N = function() {
	2 & this.f || (this.f |= 2, this.u = G, G = this);
}, Y.prototype.d = function() {
	this.f |= 8, 1 & this.f || _t(this);
}, Y.prototype.dispose = function() {
	this.d();
};
function X(e, t) {
	var n = new Y(e, t);
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
var yt, bt, xt = typeof window < "u" && !!window.__PREACT_SIGNALS_DEVTOOLS__, St = [];
X(function() {
	yt = this.N;
})();
function Z(e, t) {
	u[e] = t.bind(null, u[e] || function() {});
}
function Ct(e) {
	if (bt) {
		var t = bt;
		bt = void 0, t();
	}
	bt = e && e.S();
}
function wt(e) {
	var t = this, n = e.data, r = Et(n);
	r.name = "ReactiveDom", r.value = n;
	var i = Re(function() {
		for (var e = t, n = t.__v; n = n.__;) if (n.__c) {
			n.__c.__$f |= 4;
			break;
		}
		var i = ht(function() {
			var e = r.value.value;
			return e === 0 ? 0 : !0 === e ? "" : e || "";
		}), a = ht(function() {
			return !Array.isArray(i.value) && !f(i.value);
		}), o = X(function() {
			if (this.N = kt, a.value) {
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
wt.displayName = "ReactiveTextNode", Object.defineProperties(q.prototype, {
	constructor: {
		configurable: !0,
		value: void 0
	},
	type: {
		configurable: !0,
		value: wt
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
}), Z("__b", function(e, t) {
	if (typeof t.type == "string") {
		var n, r = t.props;
		for (var i in r) if (i !== "children") {
			var a = r[i];
			a instanceof q && (n || (t.__np = n = {}), n[i] = a, r[i] = a.peek());
		}
	}
	e(t);
}), Z("__r", function(e, t) {
	if (e(t), t.type !== j) {
		Ct();
		var n, r = t.__c;
		r && (r.__$f &= -2, (n = r.__$u) === void 0 && (r.__$u = n = function(e, t) {
			var n;
			return X(function() {
				n = this;
			}, { name: t }), n.c = e, n;
		}(function(e) {
			return function() {
				var t;
				xt && ((t = this.y) == null || t.call(this)), e.__$f |= 1, e.setState({});
			};
		}(r), typeof t.type == "function" ? t.type.displayName || t.type.name : ""))), Ct(n);
	}
}), Z("__e", function(e, t, n, r) {
	Ct(), e(t, n, r);
}), Z("diffed", function(e, t) {
	Ct();
	var n;
	if (typeof t.type == "string" && (n = t.__e)) {
		var r = t.__np, i = t.props, a = n.U;
		if (a) for (var o in a) {
			var s = a[o];
			s === void 0 || r && o in r || (s.d(), a[o] = void 0);
		}
		if (r) for (var c in a || (a = {}, n.U = a), r) {
			var l = a[c], u = r[c];
			l === void 0 ? (l = Tt(n, c, u, i), a[c] = l) : l.o(u, i);
		}
	}
	e(t);
});
function Tt(e, t, n, r) {
	var i = t in e && e.ownerSVGElement === void 0, a = dt(n);
	return {
		o: function(e, t) {
			a.value = e, r = t;
		},
		d: X(function() {
			this.N = kt;
			var n = a.value.value;
			r[t] !== n && (r[t] = n, i ? e[t] = n : n != null && (!1 !== n || t[4] === "-") ? e.setAttribute(t, n) : e.removeAttribute(t));
		})
	};
}
Z("unmount", function(e, t) {
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
}), Z("__h", function(e, t, n, r) {
	r < 3 && (t.__$f |= 2), e(t, n, r);
}), M.prototype.shouldComponentUpdate = function(e, t) {
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
function Et(e, t) {
	return Re(function() {
		return dt(e, t);
	}, []);
}
var Dt = function(e) {
	queueMicrotask(function() {
		queueMicrotask(e);
	});
};
function Ot() {
	rt(function() {
		for (var e; e = St.shift();) yt.call(e);
	});
}
function kt() {
	St.push(this) === 1 && (u.requestAnimationFrame || Dt)(Ot);
}
//#endregion
//#region src/state/quality-goals.ts
var At = "/api/quality-goals?limit=200", jt = {
	data: null,
	error: ""
}, Q = dt(jt), Mt = 0, Nt = ht(() => Q.value);
ht(() => Q.value.data?.total ?? null);
function Pt() {
	Mt += 1, Q.value = jt;
}
async function Ft(e) {
	let t = Mt += 1;
	try {
		let n = await Ce(At, e);
		return t === Mt && (Q.value = {
			data: n,
			error: ""
		}), n;
	} catch (n) {
		throw !e?.aborted && t === Mt && (Q.value = {
			data: null,
			error: P(n)
		}), n;
	}
}
//#endregion
//#region src/islands/quality-goals.tsx
var It = (e, t) => Ft(t), Lt = (e) => e.has_cover ? `/cover?code=${encodeURIComponent(e.code ?? "")}` : `/poster?id=${e.id}&c=4`;
function Rt({ openItem: t, javTitleHtml: r, javDisplayName: i, srcBadge: a }) {
	let { data: l, error: u } = Nt.value;
	if (u) return /* @__PURE__ */ V("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: n(u, {
			variant: "error",
			label: "读取失败"
		}) }
	});
	let d = l?.items ?? [];
	return d.length ? /* @__PURE__ */ V("div", {
		class: "qualitylist",
		children: d.map((e) => /* @__PURE__ */ V("article", {
			class: "qualityitem",
			children: [/* @__PURE__ */ V("button", {
				class: "qualitycover",
				type: "button",
				"aria-label": `打开 ${i(e)}`,
				onClick: () => t(e.id),
				children: /* @__PURE__ */ V("img", {
					src: Lt(e),
					alt: "",
					loading: "lazy",
					onError: (e) => e.currentTarget.remove()
				})
			}), /* @__PURE__ */ V("div", { children: [
				/* @__PURE__ */ V("h3", { children: /* @__PURE__ */ V("button", {
					type: "button",
					"data-middle-truncate": !0,
					onClick: () => t(e.id),
					dangerouslySetInnerHTML: { __html: r(e) }
				}) }),
				/* @__PURE__ */ V("p", {
					class: "mono",
					children: [
						/* @__PURE__ */ V("span", {
							style: "display:contents",
							dangerouslySetInnerHTML: { __html: a(e.location, e.cost) }
						}),
						/* @__PURE__ */ V("span", { children: o[e.location] ?? e.location }),
						/* @__PURE__ */ V("span", { children: s(e.duration) }),
						/* @__PURE__ */ V("span", { children: c(e.size ?? 0) })
					]
				}),
				e.reason ? /* @__PURE__ */ V("p", { children: e.reason }) : null
			] })]
		}, e.id))
	}) : /* @__PURE__ */ V("div", {
		class: "qualitylist",
		dangerouslySetInnerHTML: { __html: e("sparkles", "没有标记中的高清版目标", "现有版本都已满足条件，或还没有加入追踪。") }
	});
}
//#endregion
//#region src/jobs.ts
async function zt(e) {
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
function Bt(e) {
	let t = document.createElement("div");
	e.host.hidden = !0, t.dataset.followJob = "", t.setAttribute("aria-live", "polite"), e.host.prepend(t);
	let n = e.storageKey || "peach-follow-job", r = sessionStorage.getItem(n) || void 0, i = !1;
	zt({
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
var Vt = (e, t) => Ce("/api/scraping", t);
function Ht({ value: e, onChange: t }) {
	let n = B(null), i = B(t);
	return i.current = t, Le(() => {
		let t = n.current;
		t.innerHTML = r([
			["environment", "系统代理"],
			["direct", "应用直连"],
			["proxy", "自定义代理"]
		], e, { label: "连接方式" });
		let o = a(t.firstElementChild), s = () => i.current(o.value);
		return o.addEventListener("change", s), () => {
			o.disabled = !0, o.removeEventListener("change", s), t.replaceChildren();
		};
	}, []), /* @__PURE__ */ V("div", {
		ref: n,
		class: "scraping-network"
	});
}
function Ut({ source: e, toast: r }) {
	let [a, o] = z(e), [s, c] = z(e.network), [l, u] = z(""), [d, f] = z(""), [p, m] = z(""), [h, g] = z("paste"), [_, v] = z(""), [y, b] = z(!1), [x, S] = z(""), [C, w] = z([]), T = B(null), E = B(null);
	Le(() => {
		E.current?.querySelectorAll("footer button").forEach((e) => i(e, y));
	}, [y]);
	let D = B(new AbortController());
	Ie(() => () => D.current.abort(), []);
	async function O(t) {
		if (!y) {
			b(!0), S(""), w([]);
			try {
				if (t === "check") {
					let t = await F("/api/scraping/check", { source: e.source }, "POST", D.current.signal);
					D.current.signal.aborted || w(t.results);
				} else {
					let n = await F("/api/scraping/settings", {
						source: e.source,
						network: s,
						proxy: l,
						cookie: d,
						cookies_text: p,
						revoke: t === "revoke"
					}, "POST", D.current.signal);
					D.current.signal.aborted || (o(n.saved), u(""), f(""), m(""), v(""), T.current && (T.current.value = ""), r(t === "revoke" ? "Cookie 已撤销" : "来源设置已保存"));
				}
			} catch (e) {
				D.current.signal.aborted || S(P(e));
			} finally {
				D.current.signal.aborted || b(!1);
			}
		}
	}
	return /* @__PURE__ */ V("section", {
		class: "scraping-source",
		children: /* @__PURE__ */ V("form", {
			ref: E,
			class: "cleanupfieldset",
			"data-geist-fieldset": !0,
			onSubmit: (e) => {
				e.preventDefault(), O("save");
			},
			children: [/* @__PURE__ */ V("div", {
				class: "geist-fieldset-content scraping-fields",
				children: [
					/* @__PURE__ */ V("div", { dangerouslySetInnerHTML: { __html: t(`scraping-${e.source}`, e.label) } }),
					/* @__PURE__ */ V("a", {
						class: "scraping-url",
						href: e.login,
						target: "_blank",
						rel: "noopener noreferrer",
						children: e.login
					}),
					/* @__PURE__ */ V("div", {
						class: "scraping-label",
						children: ["连接方式", /* @__PURE__ */ V(Ht, {
							value: s,
							onChange: c
						})]
					}),
					s === "proxy" && /* @__PURE__ */ V("label", { children: ["代理地址", /* @__PURE__ */ V("input", {
						class: "geist-input",
						type: "password",
						autoComplete: "off",
						value: l,
						placeholder: a.proxy_saved ? "已保存，留空保留" : "http://127.0.0.1:7890",
						disabled: y,
						onInput: (e) => u(e.currentTarget.value)
					})] }),
					e.accepts_cookie && /* @__PURE__ */ V(j, { children: [
						/* @__PURE__ */ V("p", { children: a.cookie_saved ? "Cookie 已保存，登录是否有效请在抓取时确认。" : "需要登录时，任选一种方式提供 Cookie。" }),
						/* @__PURE__ */ V("div", {
							class: "insightswitch scraping-cookie-method",
							role: "radiogroup",
							"aria-label": "提供 Cookie 的方式（二选一）",
							children: [["paste", "粘贴 Cookie"], ["file", "导入文件"]].map(([t, n]) => /* @__PURE__ */ V("label", { children: [/* @__PURE__ */ V("input", {
								type: "radio",
								name: `cookie-method-${e.source}`,
								value: t,
								checked: h === t,
								onChange: () => {
									g(t), f(""), m(""), v("");
								}
							}), /* @__PURE__ */ V("span", { children: n })] }, t))
						}),
						h === "paste" ? /* @__PURE__ */ V("label", { children: ["Cookie", /* @__PURE__ */ V("input", {
							class: "geist-input",
							type: "password",
							autoComplete: "off",
							value: d,
							disabled: y,
							onInput: (e) => f(e.currentTarget.value)
						})] }) : /* @__PURE__ */ V("label", {
							class: "scraping-file",
							children: ["Netscape Cookie 文件（.txt）", /* @__PURE__ */ V("span", {
								class: "scraping-file-control",
								children: [
									/* @__PURE__ */ V("span", {
										class: "geist-button",
										children: "选择文件"
									}),
									/* @__PURE__ */ V("span", {
										class: "scraping-file-name",
										children: _ || "未选择文件"
									}),
									/* @__PURE__ */ V("input", {
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
					x && /* @__PURE__ */ V("div", {
						role: "alert",
						dangerouslySetInnerHTML: { __html: n(x, { variant: "error" }) }
					}),
					C.map((t) => /* @__PURE__ */ V("div", {
						role: "status",
						dangerouslySetInnerHTML: { __html: n(`${e.label}${t.label === "来源页面" ? "" : " 高清图片"}：${t.ok ? "可连接" : "不能连接"}` + (t.width ? ` · ${t.width} × ${t.height}` : "") + (t.message ? `。${t.message}` : ""), { variant: t.ok ? "success" : "error" }) }
					}, t.label))
				]
			}), /* @__PURE__ */ V("footer", {
				class: "geist-fieldset-footer",
				"data-geist-fieldset-footer": !0,
				children: [
					/* @__PURE__ */ V("button", {
						class: "geist-button primary",
						type: "submit",
						children: "保存"
					}),
					/* @__PURE__ */ V("button", {
						class: "geist-button",
						type: "button",
						onClick: () => void O("check"),
						children: "检查连接"
					}),
					e.accepts_cookie && a.cookie_saved && /* @__PURE__ */ V("button", {
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
function Wt({ data: e, error: r, toast: a }) {
	let [o, s] = z(""), [c, l] = z(!1), [u, d] = z(""), f = B(null);
	Le(() => i(f.current, c), [c]);
	let p = B(new AbortController()), m = B(0);
	async function h(e = !1) {
		let t = ++m.current;
		await zt({
			read: (e) => Ce("/api/scraping/cover", e),
			active: () => !p.current.signal.aborted && t === m.current,
			render: (t) => {
				l(t.status === "running"), t.status === "running" && (e = !1), t.status === "failed" && !e && d(t.error || "采集未取得"), t.status === "complete" && !e && a(t.result || "封面采集完成");
			},
			disconnected: () => d("连接中断，正在重新读取后台进度")
		});
	}
	Ie(() => (h(!0), () => p.current.abort()), []);
	async function g() {
		if (!c) {
			m.current++, l(!0), d("");
			try {
				await F("/api/scraping/cover", { code: o }, "POST", p.current.signal), await h();
			} catch (e) {
				p.current.signal.aborted || (l(!1), d(P(e)));
			}
		}
	}
	return r ? /* @__PURE__ */ V("div", {
		role: "alert",
		dangerouslySetInnerHTML: { __html: n(r, { variant: "error" }) }
	}) : /* @__PURE__ */ V("div", {
		class: "scraping-page",
		children: [
			/* @__PURE__ */ V("p", { children: "高清图片可能需要代理才能下载，请先检查连接。" }),
			/* @__PURE__ */ V("section", {
				class: "cleanupfieldset scraping-source",
				"data-geist-fieldset": !0,
				children: /* @__PURE__ */ V("div", {
					class: "geist-fieldset-content scraping-fields",
					children: [
						/* @__PURE__ */ V("div", { dangerouslySetInnerHTML: { __html: t("scraping-cover", "高清封面") } }),
						/* @__PURE__ */ V("form", {
							class: "scraping-cover-form",
							onSubmit: (e) => {
								e.preventDefault(), g();
							},
							children: [/* @__PURE__ */ V("input", {
								class: "geist-input",
								"aria-label": "馆藏番号",
								required: !0,
								value: o,
								disabled: c,
								placeholder: "输入馆藏番号，如 ABW-232",
								onInput: (e) => s(e.currentTarget.value)
							}), /* @__PURE__ */ V("button", {
								ref: f,
								class: "geist-button primary",
								type: "submit",
								children: "抓取封面"
							})]
						}),
						u && /* @__PURE__ */ V("div", {
							role: "alert",
							dangerouslySetInnerHTML: { __html: n(u, { variant: "error" }) }
						})
					]
				})
			}),
			e?.sources.map((e) => /* @__PURE__ */ V(Ut, {
				source: e,
				toast: a
			}, e.source))
		]
	});
}
//#endregion
//#region src/state/index.ts
var Gt = { "quality-goals": {
	refresh: Ft,
	reset: Pt
} }, Kt = () => Object.keys(Gt);
async function qt(e) {
	let t = Gt[e];
	if (!t) throw Error(`未登记的共享 store：${String(e)}`);
	try {
		return await t.refresh(), !0;
	} catch {
		return !1;
	}
}
//#endregion
//#region src/sidebar.ts
function Jt(e) {
	return [
		"/",
		"/unseen",
		"/watch-later",
		"/flagged",
		"/trash",
		"/junk-files"
	].includes(e) || /^\/(item|mix|parts|editions)\//.test(e) || /^\/playlists\/\d+\/\d+$/.test(e) || /^\/(performers|studios|creators|series|agencies)\/.+/.test(e);
}
function Yt(e, t) {
	return e.dataset.surface === t && e.querySelector(".dnav") ? !1 : (e.dataset.surface = t, e.replaceChildren(), !0);
}
function Xt(e) {
	let t = /* @__PURE__ */ new Map();
	for (let n of e) for (let e of new Set(n.tags || [])) t.set(e, (t.get(e) || 0) + 1);
	return [...t].sort((e, t) => t[1] - e[1]).slice(0, 30);
}
//#endregion
//#region src/islands.ts
var Zt = {
	scraping: {
		load: Vt,
		component: Wt
	},
	"quality-goals": {
		load: It,
		component: Rt
	},
	configuration: {
		load: Xe,
		component: et
	}
}, Qt = () => Object.keys(Zt), $ = /* @__PURE__ */ new Map();
async function $t(e, t, n, r = {}) {
	let i = Zt[e];
	if (!i) throw Error(`未注册的 island：${String(e)}`);
	en(t);
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
			error: P(e)
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
	be(k(i.component, s), t);
}
function en(e) {
	let t = $.get(e);
	t && (t.controller.abort(), $.delete(e), t.painted && be(null, e));
}
//#endregion
export { Bt as followJobProgress, Qt as islandNames, $t as mountIsland, qt as refreshStore, Jt as sidebarHasCatalogContent, Xt as sidebarTagCounts, Kt as storeNames, Yt as syncSidebarSurface, en as unmountIsland, zt as watchJob };
