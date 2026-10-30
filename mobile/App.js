import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Image,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";
import AsyncStorage from "@react-native-async-storage/async-storage";

import { api } from "./src/api";
import { BRAND } from "./src/config";

const LOGO = require("./assets/logo.png");
const LAST_ID_KEY = "ohr_last_student_id";

export default function App() {
  const [studentId, setStudentId] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null); // StudentStatus
  const [result, setResult] = useState(null); // last CheckResponse
  const [error, setError] = useState("");

  // Restore the last-used student ID so students don't retype it.
  useEffect(() => {
    AsyncStorage.getItem(LAST_ID_KEY).then((v) => {
      if (v) {
        setStudentId(v);
        lookup(v);
      }
    });
  }, []);

  function clearMessages() {
    setError("");
    setResult(null);
  }

  async function lookup(id) {
    const sid = (id ?? studentId).trim();
    if (!sid) return;
    clearMessages();
    setLoading(true);
    try {
      const s = await api.status(sid);
      setStatus(s);
      await AsyncStorage.setItem(LAST_ID_KEY, sid);
    } catch (e) {
      setStatus(null);
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function doAction(kind) {
    const sid = studentId.trim();
    if (!sid) {
      setError("Please enter your Student ID.");
      return;
    }
    clearMessages();
    setLoading(true);
    try {
      let res;
      if (kind === "in") res = await api.checkIn(sid);
      else if (kind === "out") res = await api.checkOut(sid);
      else res = await api.check(sid); // toggle
      setResult(res);
      setStatus({
        student_id: res.student_id,
        full_name: res.student_name,
        is_present: res.is_present,
        last_action: res.action,
        last_timestamp: res.timestamp,
      });
      await AsyncStorage.setItem(LAST_ID_KEY, sid);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const present = status?.is_present;

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar style="light" />
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          {/* Branded header */}
          <View style={styles.header}>
            <Image source={LOGO} style={styles.logo} resizeMode="contain" />
            <Text style={styles.he}>{BRAND.nameHe}</Text>
            <Text style={styles.school}>{BRAND.school}</Text>
            <Text style={styles.subtitle}>Student Sign In / Sign Out</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.label}>Student ID</Text>
            <TextInput
              style={styles.input}
              value={studentId}
              onChangeText={setStudentId}
              placeholder="e.g. 1001"
              placeholderTextColor="#9aa4b2"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="default"
              returnKeyType="search"
              onSubmitEditing={() => lookup()}
            />
            <TouchableOpacity style={styles.lookupBtn} onPress={() => lookup()}>
              <Text style={styles.lookupText}>Check Status</Text>
            </TouchableOpacity>

            {status && (
              <View style={styles.statusBox}>
                <Text style={styles.statusName}>{status.full_name}</Text>
                <View
                  style={[
                    styles.statusPill,
                    { backgroundColor: present ? "#e3f6ea" : "#eef1f6" },
                  ]}
                >
                  <Text
                    style={[
                      styles.statusPillText,
                      { color: present ? BRAND.green : "#6b7280" },
                    ]}
                  >
                    {present ? "● Currently Signed In" : "○ Currently Signed Out"}
                  </Text>
                </View>
              </View>
            )}

            {/* Action buttons */}
            <View style={styles.actions}>
              <TouchableOpacity
                style={[styles.btn, { backgroundColor: BRAND.green }]}
                onPress={() => doAction("in")}
                disabled={loading}
              >
                <Text style={styles.btnText}>Sign In</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.btn, { backgroundColor: BRAND.red }]}
                onPress={() => doAction("out")}
                disabled={loading}
              >
                <Text style={styles.btnText}>Sign Out</Text>
              </TouchableOpacity>
            </View>

            {loading && <ActivityIndicator color={BRAND.blue} style={{ marginTop: 16 }} />}

            {result && (
              <View style={styles.resultOk}>
                <Text style={styles.resultTitle}>
                  {result.action === "in" ? "✓ Signed In" : "✓ Signed Out"}
                </Text>
                <Text style={styles.resultMsg}>{result.message}</Text>
                <Text style={styles.resultTime}>
                  {new Date(result.timestamp).toLocaleString()}
                </Text>
              </View>
            )}

            {error ? (
              <View style={styles.resultErr}>
                <Text style={styles.errText}>{error}</Text>
              </View>
            ) : null}
          </View>

          <Text style={styles.footer}>
            {BRAND.school} · {BRAND.nameHe}
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: BRAND.navy },
  scroll: { flexGrow: 1, backgroundColor: BRAND.bg },
  header: {
    backgroundColor: BRAND.navy,
    alignItems: "center",
    paddingTop: 24,
    paddingBottom: 30,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  logo: {
    width: 150,
    height: 110,
    backgroundColor: "#fff",
    borderRadius: 14,
    padding: 6,
  },
  he: { color: BRAND.goldLight, fontSize: 18, marginTop: 10, fontWeight: "600" },
  school: { color: "#fff", fontSize: 22, fontWeight: "800", marginTop: 2 },
  subtitle: { color: "#cdd7e8", fontSize: 14, marginTop: 4 },
  card: {
    backgroundColor: "#fff",
    margin: 18,
    borderRadius: 16,
    padding: 22,
    shadowColor: "#000",
    shadowOpacity: 0.08,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 3 },
    elevation: 3,
  },
  label: { color: "#6b7280", fontSize: 13, marginBottom: 6, fontWeight: "600" },
  input: {
    borderWidth: 1,
    borderColor: "#e3e8f0",
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 18,
    color: BRAND.navy,
  },
  lookupBtn: {
    marginTop: 10,
    alignSelf: "flex-start",
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: BRAND.blue,
  },
  lookupText: { color: BRAND.blue, fontWeight: "600", fontSize: 13 },
  statusBox: {
    marginTop: 18,
    alignItems: "center",
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: "#eef1f6",
  },
  statusName: { fontSize: 18, fontWeight: "700", color: BRAND.navy, marginBottom: 8 },
  statusPill: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 999 },
  statusPillText: { fontWeight: "700", fontSize: 13 },
  actions: { flexDirection: "row", gap: 12, marginTop: 20 },
  btn: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  btnText: { color: "#fff", fontSize: 17, fontWeight: "800" },
  resultOk: {
    marginTop: 18,
    backgroundColor: "#e3f6ea",
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: "#b8e4c6",
  },
  resultTitle: { color: BRAND.green, fontWeight: "800", fontSize: 16 },
  resultMsg: { color: "#1f2937", marginTop: 4, fontSize: 15 },
  resultTime: { color: "#6b7280", marginTop: 4, fontSize: 12 },
  resultErr: {
    marginTop: 18,
    backgroundColor: "#fdecec",
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: "#f3c0c0",
  },
  errText: { color: BRAND.red, fontWeight: "600" },
  footer: { textAlign: "center", color: "#9aa4b2", fontSize: 12, padding: 20 },
});
